import random
from typing import Annotated

from starlette import status
from starlette.responses import RedirectResponse

from fastapi import Depends, HTTPException, APIRouter, status, Request
from database.models import Users, Words, Translations, UserPoints
from database.db_connection import Database
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Engine, and_, select, update
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from .auth import get_current_user, get_user_exception

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

@router.get("/{src_lang}/{target_lang}/{nr_words}")
async def play(
               user: user_dependency, src_lang:str='EN',
               target_lang: str = "PL", nr_words:int = 4,
               eng: Engine = Depends(get_db)):
               
    src_lang = src_lang.upper()
    target_lang = target_lang.upper()

    if user is None:
        print("User is None")
        #raise get_user_exception()
    words = {}
    bag = set()
    with Session(eng) as session:
        stmt = select(Words.wrd_id).filter(Words.wrd_lang.\
                                          in_([src_lang, target_lang]))
        word_list = list(session.execute(stmt).scalars())
        random_id = random.randint(0, (len(word_list) - 1))
        drawed_word = word_list[random_id]
        stmt = select(Words.wrd_id, Words.wrd_word, Words.wrd_lang).\
        join(Translations,Translations.trn_lang_from_fkey == Words.wrd_id).\
                                        filter(Words.wrd_id == drawed_word)
        result = session.execute(stmt).one()
        
        word_id, word, lang = result
        lng = target_lang if lang == src_lang else src_lang

        #get translation for drawed word
        stmt = select(Words.wrd_word).join(Translations,
                                          Translations.trn_lang_from_fkey==word_id).\
            filter(and_(Words.wrd_id == Translations.trn_lang_to_fkey,
                        Words.wrd_lang == lng))
        
        translated_word = session.execute(stmt).scalar_one()

        # selecting words with opposite translation to drawed word
        if lang == src_lang:
            stmt = select(Words.wrd_word).distinct()\
                .filter(Words.wrd_lang == target_lang)
        else:
            stmt = select(Words.wrd_word).distinct()\
                .filter(Words.wrd_lang == src_lang)
        result = list(session.execute(stmt).scalars())

        # adding translated word to set
        bag.add(translated_word)

        # adding words to bag until len of set will be equals with
        # the number of words required 

        while len(bag) < nr_words:
            bag.add(random.choice(result))
        for element in list(bag):
            if element == translated_word:
                words.update({element: "correct"})
            else:
                words.update({element: "incorrect"})
    
    return {"word": word, "words_bag": words}

@router.post("/action/{action}")
async def substract_the_coin(action:str, user: user_dependency, eng: Engine = Depends(get_db)):
    if user is None:
        get_user_exception()
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

    return {"status": f"{action}ed"}