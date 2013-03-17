# -*- coding: utf8 -*-

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, BigInteger, String, Unicode, Text, UnicodeText, ForeignKey, Boolean
from sqlalchemy import ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class Work_Categories(Base):
    """Mapping for Work_Categories table"""
    __tablename__ = 'work_categories'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    code = Column(UnicodeText, nullable=False)


class Work(Base):
    """Mapping for Work table"""
    __tablename__ = 'work'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey(Work_Categories.id), doc='Link to category')
    number = Column(String(10))
    name = Column(Unicode(255))
    location = Column(Unicode(50))
    colophon = Column(UnicodeText)
    concordance = Column(Unicode(50))
