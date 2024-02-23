import random
from database.models import Words, Translations, UserPoints
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Engine, and_, func, or_, select


class Game:
    def __init__(self, eng:Engine, lang_1:str, lang_2:str, user_id:(int|None)=None, nr_of_words:int=4) -> None:
        self.session = Session(eng)
        self.lang_1 = "EN" if lang_1.upper() in ["EN", "EN-GB", "EN-US"] else lang_1.upper()
        self.lang_2 = "EN" if lang_2.upper() in ["EN", "EN-GB", "EN-US"] else lang_2.upper()
        try:
            stmt = select(func.count()).select_from(Words).filter(Words.wrd_lang == lang_2)
            result = self.session.execute(stmt).scalar_one_or_none()
            if result < nr_of_words:
                self.nr_of_words = result
            else:
                self.nr_of_words = nr_of_words
        except SQLAlchemyError as sql_err:
            return False

        
    
    def play(self):
        stmt = select(Words.wrd_word, Translations.trn_lang_to_fkey, Words.wrd_lang).join(Translations, Translations.trn_lang_from_fkey == Words.wrd_id).\
            filter(and_(Words.wrd_lang.in_([self.lang_1, self.lang_2]), or_(Translations.trn_translation == self.lang_1 + "->" + self.lang_2,
                                                                            Translations.trn_translation == self.lang_2 + "->" + self.lang_1)))
        word_list = list(self.session.execute(stmt).fetchall())
        drawn_id = random.randint(0, (len(word_list) - 1))
        drawn_word_data = word_list[drawn_id]
        drawn_word, translation_id, _ = drawn_word_data

        stmt = select(Words.wrd_word, Words.wrd_lang).filter(Words.wrd_id == translation_id)
        translated_word, translated_lang = self.session.execute(stmt).fetchone()

        words = self._drawn_words(drawn_word=drawn_word, translated_lang=translated_lang)
        words_bag = {}
        mixed_bag_of_words = set()
        words_to_draw = list(words)
        mixed_bag_of_words.add(translated_word)
        if len(words_to_draw) == 0:
            words = self._drawn_words(drawn_word=drawn_word, translated_lang=translated_lang)
            words_to_draw = list(words)
        while len(mixed_bag_of_words) < self.nr_of_words:
            try:            
                drawn_id = random.randint(0, (len(words_to_draw) -1))
                mixed_bag_of_words.add(words_to_draw.pop(drawn_id))
            except ValueError:
                break  

            
        for element in mixed_bag_of_words:
            if element == translated_word:
                words_bag.update({element: "correct"})
            else:
                words_bag.update({element: "incorrect"})
        
        return {"word": drawn_word, "words_bag": words_bag}
    
    def _drawn_words(self, drawn_word: str, translated_lang:str):
        stmt = select(Translations.trn_lang_to_fkey).join(Words, Words.wrd_id == Translations.trn_lang_from_fkey)\
        .filter(Words.wrd_word == drawn_word)
        forbidden_ids = tuple(element for element in self.session.execute(stmt).scalars())
       
        stmt = select(Words.wrd_word).filter(and_(Words.wrd_lang == translated_lang, Words.wrd_id.not_in(forbidden_ids)))
        words = tuple(element for element in self.session.execute(stmt).scalars())
        return words

    def __del__(self):
        self.session.close()    
