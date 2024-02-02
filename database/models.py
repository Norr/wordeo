from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, DATE, DATETIME, TEXT
from datetime import date, datetime

class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = "users"

    usr_id: Mapped[int] = mapped_column(INTEGER, primary_key=True,
                                         autoincrement=True,
                                         nullable=False)
    usr_name: Mapped[str] = mapped_column(VARCHAR(50),
                                          nullable=False)
    usr_password: Mapped[str] = mapped_column(VARCHAR(100),
                                              nullable=False)
    usr_email: Mapped[str] = mapped_column(VARCHAR(100),
                                           nullable=False,
                                           unique=True)
    usr_registration_date: Mapped[date] = mapped_column(DATE,
                                                        nullable=False)
    

class Words(Base):
    __tablename__ = "words"

    wrd_id: Mapped[int] = mapped_column(INTEGER,
                                        primary_key=True,
                                        nullable=False,
                                        autoincrement=True)
    wrd_word: Mapped[str] = mapped_column(VARCHAR(100),
                                          nullable=False)
    wrd_lang: Mapped[str] = mapped_column(VARCHAR(5),
                                          nullable=False)
    
class Translations(Base):
    __tablename__ = "translations"

    trn_id: Mapped[int] = mapped_column(INTEGER,
                                        primary_key=True,
                                        nullable=False,
                                        autoincrement=True)
    trn_lang_from_fkey: Mapped[int] = mapped_column(INTEGER,
                                                    ForeignKey('word.wrd_id'),
                                                    nullable=False)
    trn_lang_to_fkey: Mapped[int] = mapped_column(INTEGER,
                                                  ForeignKey('word.wrd_id'),
                                                  nullable=False)
    word_1 = relationship("Word", foreign_keys=[trn_lang_from_fkey])
    word_2 = relationship("Word", foreign_keys=[trn_lang_to_fkey])
    
class UserPoints(Base):
    __tablename__ = "users_points"

    usr_pnt_id: Mapped[int] = mapped_column(INTEGER,
                                            primary_key=True,
                                            nullable=False,
                                            autoincrement=True)
    usr_pnt_value: Mapped[int] = mapped_column(INTEGER,
                                               nullable=False)
    usr_pnt_usr_id: Mapped[int] = mapped_column(INTEGER,
                                                ForeignKey('users.usr_id'),
                                                nullable=False)
    user = relationship('Users', foreign_keys=[usr_pnt_usr_id])

class Logs(Base):
    __tablename__ = "logs"

    log_id:Mapped[int] = mapped_column(INTEGER,
                                       primary_key=True,
                                       nullable=False,
                                       autoincrement=True)
    log_text:Mapped[str] = mapped_column(TEXT,
                                         nullable=False)
    log_occured:Mapped[datetime] = mapped_column(DATETIME,
                                                 nullable=False)