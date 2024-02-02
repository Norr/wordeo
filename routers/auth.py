import sys
sys.path.append("..")

import os
from fastapi import Depends, HTTPException, status, APIRouter
from pydantic import BaseModel, Field, EmailStr
from typing import Annotated, Optional
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from passlib.context import CryptContext
from database.db_connection import Database
from database.models import Users, UserPoints
from sqlalchemy.orm import Session
from sqlalchemy import Engine, select
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
#from jose import jwt, JWTError
from authlib.jose import jwt, JoseError




load_dotenv()

SECRET_KEY =os.getenv("T_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_regex = r"[A-Za-z0-9!@#$%^&*()_+={}?:~\[\] ]{8,32}"


class CreateUser(BaseModel):
    username: str = Field(description="The username must be between 4-10 alphanumeric digests.", pattern=r'[A-Za-z0-9_-]{4,10}')
    email: EmailStr
    password: str = Field(..., pattern=password_regex)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
    user_id: int | None = None

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


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
        user_stmt = select(Users).filter(Users.usr_name == username)
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
        expire = datetime.utcnow() + timedelta(minutes=15)
    payload.update({"exp": expire})
    return jwt.encode(header=header, payload=payload, key=SECRET_KEY)
    #return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        #payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        payload = jwt.decode(s=token, key=SECRET_KEY)
        username: str = payload.get("usr")
        user_id: int = payload.get("id")
        return {"username": username, "id": user_id}
    #except JWTError:
    except JoseError:
        raise credentials_exception
   
    # username: str = payload.get("usr")
    # user_id: int = payload.get("id")
    # if username is None or user_id is None:
    #     print("get current user error because user is None or user_id is None")
    #     raise get_user_exception()
    # return {"username": username, "id": user_id}
    # except BaseException as ex:
    #     print(f"Exception of jwt.payload, function get_current_user().")
    #     raise get_user_exception()
    
@router.post("/user/add")
async def create_new_user(create_user: CreateUser, eng: Engine = Depends(get_db), status_code=status.HTTP_201_CREATED):
        
        try:
            with Session(eng) as session:
                create_user_model = Users()
                create_user_model.usr_name = create_user.username
                create_user_model.usr_email = create_user.email
                create_user_model.usr_registration_date = datetime.now()
                
                hash_password = get_password_hash(create_user.password)
                create_user_model.usr_password = hash_password       
        
                session.add(create_user_model)
                session.commit()

                added_user_id = create_user_model.usr_id
                new_user_points = UserPoints()
                new_user_points.usr_pnt_usr_id = added_user_id
                new_user_points.usr_pnt_value = 0
                session.add(new_user_points)
                session.commit()
            
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User with the email"\
                                f" {create_user.email} or the username {create_user.username} exists.")

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                 eng: Engine = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, eng)
    if not user:
        raise token_exception()
    token_expires = timedelta(minutes=20)
    token = create_access_token(user.usr_name,
                                user.usr_id,
                                expires_delta=token_expires)
    return Token(access_token=token, token_type="bearer")

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