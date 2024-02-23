import os
import deepl
import yaml

from database.models import Words, Translations
from database.db_connection import Database
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Engine, and_, func, select, delete
from dotenv import load_dotenv


DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')
translator = deepl.Translator(DEEPL_API_KEY)
with open(file="languages.yaml", mode='r') as languages:
    LANGUAGES = yaml.safe_load(languages)['available_languages']

class MakeTranslation:
    def __init__(self, eng:Engine, translator=deepl.Translator(DEEPL_API_KEY) ) -> None:
        self.eng:Engine = eng
        translator = translator
        self.session = Session(self.eng)
        self.lang_from = ""
        self.lang_to = ""

    def translate(self, word_to_translate:str, source_language:str="PL", 
                  target_language:str="EN-US"):
        global word_to_translate_id
        eng = self.eng
        if source_language == "":
            return {"error": "Source language cannot be empty."}
        if target_language == "":
            return {"error": "Target language cannot be empty."}
        if source_language not in LANGUAGES:
            return {"error": f"Language from ({source_language}) is not supported."}        
        if target_language not in LANGUAGES:
            return {"error": f"Language to ({target_language}) is not supported."}
        if word_to_translate == "":
            return {"error": "Nothing to translate"}
        
        
        self.lang_from = source_language.upper()
        self.lang_to = target_language.upper()
        

        #checking if word exists in database
        word_to_translate_id = self._checking_if_word_existd_in_database(word_to_translate)
        if word_to_translate_id is None:
            
            word_to_translate_id = self._add_word_to_database(word=word_to_translate, lang=self.lang_from)

            translated_word_id  = self._translate_word(word=word_to_translate,
                                                     src_lang=self.lang_from,
                                                     target_lang=self.lang_to)
            if translated_word_id is False:
                return {"error": f"Can't translate word {word_to_translate}. Languages are mixed up."}
            
            self._add_tranlations_to_translations_table(key_from=word_to_translate_id,
                                                       key_to=translated_word_id)
            
       
        elif len(self._check_if_translation_exists(word=word_to_translate,
                                               target_lang=self.lang_to)) == 0:
            
            if not  self._check_if_the_languages_have_not_been_mixed_up(word=word_to_translate, translation_from=self.lang_from):
                return {"error": f"Can't translate word {word_to_translate}. Languages are mixed up."}
            translated_word_id = self._translate_word(word=word_to_translate,
                                                     src_lang=self.lang_from,
                                                     target_lang=self.lang_to) 
            self._add_tranlations_to_translations_table(key_from=word_to_translate_id,
                                                       key_to=translated_word_id)
        return  self._check_if_translation_exists(word=word_to_translate,
                                               target_lang=self.lang_to)
    
    
    def _checking_if_word_existd_in_database(self, word:str) -> (int|None):        
        try:
            stmt = select(Words.wrd_id).filter(func.lower(Words.wrd_word) == word.lower())
            word_id = self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError:
                return {"error": f"Can't translate word {word}"}
        return word_id
        
    def _add_word_to_database(self, word:str, lang:str) -> int:
        try:
            new_word = Words()
            new_word.wrd_lang = lang.upper()
            new_word.wrd_word = word
            self.session.add(new_word)
            self.session.commit()
        except SQLAlchemyError:
            return {"error": f"Can't translate word {word}"}
        return new_word.wrd_id
    
    def _translate_word(self, word:str, src_lang:str, target_lang:str) -> str:
        
        try:
            translated_word = str(translator.translate_text(text=word,
                                                    source_lang=src_lang,
                                                    target_lang=target_lang))
            if translated_word == word:
                stmt = delete(Words).filter(Words.wrd_id == word_to_translate_id)
                self.session.execute(stmt)
                self.session.commit()
                return False
        except BaseException as ex:
            return{"error": ex}
        return self._add_word_to_database(word=translated_word, 
            lang="EN" if target_lang in ["EN-GB", "EN-US", "EN"] else target_lang)
    
    def _add_tranlations_to_translations_table(self, key_from: int, key_to: int):
        try:
            lang_from = "EN" if self.lang_from in ["EN-GB", "EN-US", "EN"] else self.lang_from
            lang_to = "EN" if self.lang_to in ["EN-GB", "EN-US", "EN"] else self.lang_to
            # adding relation between searched word and translated word
            new_translation = Translations()
            new_translation.trn_lang_from_fkey = key_from
            new_translation.trn_lang_to_fkey = key_to
            new_translation.trn_translation = f"{lang_from}->{lang_to}"
            self.session.add(new_translation)
            self.session.commit()

            # adding relation between translated word and searched word
            # to the database
            new_translation = Translations()
            new_translation.trn_lang_from_fkey = key_to
            new_translation.trn_lang_to_fkey = key_from
            new_translation.trn_translation = f"{lang_to}->{lang_from}"
            self.session.add(new_translation)
            self.session.commit()
        except SQLAlchemyError:
            return {"error": f"Can't translate word"}
    def _check_if_translation_exists(self, word:str, target_lang:str) -> (list|None):
        try:
            target_lang = "EN" if target_lang in ["EN-GB", "EN-US", "EN"] else target_lang
            # getting id from column trn_lang_to from table Translatione where
            # trn_lang_from_fkey equals id of searched word
            subquery = select(Translations.trn_lang_to_fkey)\
            .join(Words, Translations.trn_lang_from_fkey == Words.wrd_id)\
            .filter(func.lower(Words.wrd_word)==word.lower()).scalar_subquery()

            #Getting word from table Word where word id equal trn_lang_to_fk
            smt = select(Words.wrd_word).filter(and_(Words.wrd_id.in_(subquery), Words.wrd_lang==target_lang))

            result_of_query = self.session.execute(smt).scalars()
            result = [element for element in result_of_query]
        except SQLAlchemyError:
            return {"error": f"Can't translate word {word}"}
        return result
    
    def _check_if_the_languages_have_not_been_mixed_up(self, word:str, translation_from:str) -> bool:
        stmt = select(Words.wrd_lang).filter(Words.wrd_word == word).distinct()
        language_of_word = self.session.execute(stmt).scalar_one_or_none()
        if translation_from != language_of_word:
            return False
        return True

    
    
    def __del__(self):
        self.session.close()
