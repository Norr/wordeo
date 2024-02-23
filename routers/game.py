from typing import Annotated



from fastapi import Depends, APIRouter,  Request
from database.models import UserPoints
from database.db_connection import Database
from sqlalchemy.orm import Session
from sqlalchemy import Engine, select, update
from dotenv import load_dotenv
from .auth import get_current_user, get_user_exception
from game.game import Game


router = APIRouter(
    prefix="/game",
    tags=["game"],
    responses={404: {"description": "User not found"}}
)


def get_db():
    try:
        eng = Database()._get_engine()
        yield eng
    finally:
        ...

user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/get_user_points")
async def get_user_points(request: Request, eng:Engine = Depends(get_db), ):
    user = await get_current_user(request)
    with Session(eng) as session:
        stmt = select(UserPoints.usr_pnt_value).\
            filter(UserPoints.usr_pnt_usr_id == user.get("id"))
        points = session.execute(stmt).scalar_one()
    return {"points": points}

@router.get("/{src_lang}/{target_lang}/{nr_words}")
async def play(
                request: Request,
                src_lang:str='EN',
                target_lang: str = "PL", nr_words:int = 4,
                eng: Engine = Depends(get_db)):               
   
    user = await get_current_user(request)
    if user is None:
        print("User is None")
    src_lang = src_lang.upper()
    target_lang = target_lang.upper()
    game = Game(eng=eng, lang_1=src_lang, lang_2=target_lang)
    return game.play()


@router.post("/action/{action}")
async def substract_the_coin(request: Request, action:str, eng: Engine = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
       return False
    else:
        user_id =  int(user.get("id"))
        with Session(eng) as session:
            stmt = select(UserPoints.usr_pnt_value)\
                .filter(UserPoints.usr_pnt_usr_id == user_id)
            points = session.execute(stmt).scalar_one_or_none()
                     
            if action == "add":
                points += 1
            elif action == "substract":
                points -= 1
            stmt = (update(UserPoints).
                        where(UserPoints.usr_pnt_usr_id == user_id).
                        values(usr_pnt_value = points))
            session.execute(stmt)
            session.commit()

    return {"coin_count": points}