import os
import sys
import deepl

from fastapi import Depends, APIRouter


from database.db_connection import Database

from sqlalchemy import Engine, func, select

from dotenv import load_dotenv
import translation.translation as trnsl

sys.path.append("..")
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')
translator = deepl.Translator(DEEPL_API_KEY)
LANGUAGES = ["PL", "EN-GB", "EN-US", "EN", "DE"]

router = APIRouter(
    prefix="/translate",
    tags=["translate"],
    responses={404: {"description": "User not found"}}
)

load_dotenv()

def get_db():
    """Function responsible for executing database.

    Yields:
        Engine: return Engine object of SQLAlchemy
    """
    try:
        eng = Database()._get_engine()
        yield eng
    finally:
        ...
        
@router.get("/{word}/{source_lang}/{target_lang}")
async def translate(word: str,
                    source_lang: str,
                    target_lang: str,
                    eng: Engine = Depends(get_db)                    
                    ):
    translation= trnsl.MakeTranslation(eng=eng)
    result = translation.translate(
        word_to_translate=word,
        source_language=source_lang,
        target_language=target_lang
    )
    return  {'translation': result}