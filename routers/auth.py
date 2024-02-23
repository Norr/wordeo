import sys
sys.path.append("..")

import os
import validators
import json
import requests

from fastapi import Depends, HTTPException, status, APIRouter, Request, Response
from fastapi import Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Annotated, Optional
from passlib.context import CryptContext
from datetime import datetime, timedelta
from database.db_connection import Database
from database.models import Users, UserPoints
from sqlalchemy.orm import Session
from sqlalchemy import Engine, func, or_, select
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from jose import jwt, JWTError, exceptions
from password_validator import PasswordValidator
from starlette.responses import RedirectResponse


load_dotenv()

SECRET_KEY =os.getenv("T_KEY")
ALGORITHM = "HS256"
RECAPATCHA_KEY=os.getenv("RECAPTCHA_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

password_schema = PasswordValidator().min(8)\
    .max(32)\
    .has().uppercase()\
    .has().lowercase()\
    .has().digits()\
    .has().no().spaces()\
    .has().symbols()
username_schema = PasswordValidator().min(4)\
.max(10)\
.has().no().symbols()\
.has().no().spaces()

templates = Jinja2Templates(directory="templates")

class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("email")
        self.password = form.get("password")
class Token(BaseModel):
    access_token: str
    token_type: str

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

def verify_recaptcha(token):
        recaptcha_url = 'https://www.google.com/recaptcha/api/siteverify'
        payload = {
           'secret': RECAPATCHA_KEY,
           'response': token
        }
        response = requests.post(url=recaptcha_url, data=payload)
        result = response.json()
        return result.get('success', False)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"user": "Not authorized"}})


def get_db():
    try:
        eng = Database()._get_engine()
        yield eng
    finally:
        ...

def get_password_hash(password):
    return bcrypt_context.hash(password)

def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str, eng):
    with Session(eng) as session:
        user_stmt = select(Users).filter(or_(Users.usr_name == username,
                                             Users.usr_email == username))
        user = session.execute(user_stmt).scalar_one()
               
    if not user:
        return False
    if not verify_password(password, user.usr_password):
        return False
    return user

def create_access_token(username: str, user_id: int,
                        expires_delta: Optional[timedelta] = None):
    header = {'alg': ALGORITHM}
    payload = {"usr": username, "id": user_id}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("usr")
        user_id: int = payload.get("id")
        return {"username": username, "id": user_id}
    except exceptions.ExpiredSignatureError:
        return "Session expired"
    except JWTError as ext:
        raise HTTPException(status_code=404, detail=f"Error: {ext}")
@router.get("/check_username/{username}")
async def check_username(username:str, eng: Engine = Depends(get_db)):
    if not username_schema.validate(username):
        return {"result": "invalid username"}
    with Session(eng) as session:
        stmt = select(Users.usr_id).filter(func.lower(Users.usr_name) == username.lower())
        result = session.execute(stmt).scalar_one_or_none()
        if result is not None:
            return {"result": "username exists"}
        return {"result": "username not exists"}
    
@router.get("/check_email/{email}")
async def check_email(email:str, eng: Engine = Depends(get_db)):
    with Session(eng) as session:
        stmt = select(Users.usr_id).filter(func.lower(Users.usr_email) == email.lower())
        result = session.execute(stmt).scalar_one_or_none()
        if result is not None:
            return {"result": "email exists"}
        return {"result": "email not exists"}

@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/", response_class=HTMLResponse)
async def login_page(request: Request, eng: Engine = Depends(get_db)):
    try:
        form = LoginForm(request=request)
        await form.create_oauth_form()
        response = RedirectResponse(url="/home", status_code=status.HTTP_302_FOUND)
        validate_user_cookie = await login_for_access_token(response=response,
                                                            form_data=form,
                                                            eng=eng)
        
        if not validate_user_cookie:
            print(f"Valid user vooke: {validate_user_cookie}")
            msg = "Incorrect username or password"
            return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
        return response
    except HTTPException:
        msg = "Unknown Error"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
        
    except HTTPException:
        msg = "Unknown Error"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    
@router.get("/logout")
async def logout(request: Request):
    msg = "Logout Successful"
    response = templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    response.delete_cookie(key="access_token")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register_user(request: Request, 
                        response: Response,
                        token:str = Form(...),
                        email: str = Form(...), username: str = Form(...),
                        eng: Engine = Depends(get_db), 
                        password: str = Form(...), verify_password: str = Form(...),                                                
                        status_code=status.HTTP_201_CREATED):
        
        email_validation = validators.email(email)
        username_validation = username_schema.validate(username)
        password_validation = password_schema.validate(password)
        
        if password != verify_password:
            response.status_code = status.HTTP_406_NOT_ACCEPTABLE
            return {"user_creation_error": "passwords not match"}
        elif not username_validation:
           response.status_code = status.HTTP_406_NOT_ACCEPTABLE
           return {"user_creation_error": "invalid username"}
        elif not password_validation:
            response.status_code = status.HTTP_406_NOT_ACCEPTABLE
            return {"user_creation_error": "invalid password"}
        elif not email_validation:
            response.status_code = status.HTTP_406_NOT_ACCEPTABLE
            return {"user_creation_error": "invalid email"}
        
        try:
            if verify_recaptcha(token=token):
                with Session(eng) as session:
                    create_user_model = Users()
                    create_user_model.usr_name = username
                    create_user_model.usr_email = email
                    create_user_model.usr_registration_date = datetime.now()
                    
                    hash_password = get_password_hash(password)
                    create_user_model.usr_password = hash_password       
            
                    session.add(create_user_model)
                    session.commit()

                    added_user_id = create_user_model.usr_id
                    new_user_points = UserPoints()
                    new_user_points.usr_pnt_usr_id = added_user_id
                    new_user_points.usr_pnt_value = 0
                    session.add(new_user_points)
                    session.commit()
                    msg = "User successfully created"
                    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
            else:
                msg = "Something went wrong, please try later."
                return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
            
        except IntegrityError:
            msg = f"User with the email {email} or the username {username} exists."
            return templates.TemplateResponse("register.html", {"request": request, "msg": msg},
                                              status_code=status.HTTP_409_CONFLICT)
      
@router.post("/token")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(),
                                 eng: Engine = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, eng)
    if not user:
        return False
    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(user.usr_name,
                                user.usr_id,
                                expires_delta=token_expires)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return True

#Exceptions
def get_user_exception():
    print("get_user_exception")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return credentials_exception


def token_exception():
    print("tocken_exception")
    token_exception_response = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return token_exception_response