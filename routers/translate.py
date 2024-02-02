import os
import deepl

from fastapi import Depends, HTTPException, APIRouter, status, Request
from database.models import Users, Words, Translations, UserPoints
from database.db_connection import Database
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Engine, select
from pydantic import BaseModel, Field
from dotenv import load_dotenv


DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')
translator = deepl.Translator(DEEPL_API_KEY)
LANGUAGES = ["PL", "EN-GB", "EN-US", "EN"]

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
    with Session(eng) as session:
        # formatting source language
        source_lang = source_lang.upper()
        # formatting target language 
        target_lang = "EN-US" if target_lang.upper() == "EN" else target_lang.upper()
        # formatting word to lower case
        word = word.lower() 
        try:
            # getting id from column trn_lang_to from table Translatione where
            # trn_lang_from_fkey equals id of searched word
            subquery = select(Translations.trn_lang_to_fkey)\
            .join(Words, Translations.trn_lang_from_fkey == Words.wrd_id)\
            .filter(Words.wrd_word==word.lower()).scalar_subquery()

            #Getting word from table Word where word id equal trn_lang_to_fk
            smt = select(Words.wrd_word).filter(Words.wrd_id == subquery)

            result = session.execute(smt).scalar_one_or_none()
            
        except SQLAlchemyError:
            print("Exeption no 1")

        # It is mean there is no searched word in the database
        # This is first translation of searched word
        
        if result is None:  
            try:
                if source_lang in LANGUAGES and target_lang in LANGUAGES:
                    # translating word using DeepL API
                    translated_word = translator.translate_text(text=word,
                                                    source_lang=source_lang,
                                                    target_lang=target_lang)
                    try:
                        with Session(eng) as session:

                            # adding searched word to the database
                            word_from = Words()
                            word_from.wrd_lang = "EN" if source_lang\
                                in ["EN-GB", "EN-US", "EN"] else source_lang
                            word_from.wrd_word = word.lower()
                            session.add(word_from)
                            session.commit()
                            word_1 = word_from.wrd_id

                            # checking whether the translation exists in the database
                            stmt = select(Words.wrd_id, Words.wrd_word)\
                                .filter(Words.wrd_word == translated_word.text.lower())
                            translated_word_exists = session.execute(stmt)\
                                .scalar_one_or_none()

                            # if translation not exists, adding the new one to the database
                            if translated_word_exists is None:
                                
                                word_to = Words()
                                word_to.wrd_lang = "EN" if target_lang in ["EN-GB", "EN-US", "EN"] else target_lang
                                word_to.wrd_word = translated_word.text.lower()
                                session.add(word_to)
                                session.commit()
                                word_2 = word_to.wrd_id
                                
                            else:
                                # if translation exists, use the id of translated word found
                                word_2 = translated_word_exists
                                
                            # adding relation between searched word and translated word
                            new_translation = Translations()
                            new_translation.trn_lang_from_fkey = word_1
                            new_translation.trn_lang_to_fkey = word_2
                            session.add(new_translation)
                            session.commit()

                            # adding relation between translated word and searched word
                            # to the database
                            new_translation = Translations()
                            new_translation.trn_lang_from_fkey = word_2
                            new_translation.trn_lang_to_fkey = word_1
                            session.add(new_translation)
                            session.commit()

                            result = translated_word.text
                    except SQLAlchemyError:
                        print("Exception no 3")
            except BaseException:
                print("Exception deepl")
        return f'{{"word_from": "{word.lower()}", "translated_word": "{result}"}}'