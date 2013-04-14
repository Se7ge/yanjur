# -*- coding: utf8 -*-

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Unicode, UnicodeText, ForeignKey, Boolean
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
    category_id = Column(Integer, ForeignKey(Work_Categories.id), doc='Link to category', nullable=False)
    number = Column(String(10), nullable=False)
    name = Column(Unicode(255), nullable=False)
    location = Column(Unicode(50))
    colophon = Column(UnicodeText)
    concordance = Column(Unicode(50))


class Action(Base):
    """Mapping for Action table"""
    __tablename__ = 'action'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)


class Place(Base):
    """Mapping for Place table"""
    __tablename__ = 'place'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)


class Title(Base):
    """Mapping for Title table"""
    __tablename__ = 'title'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)


class Person(Base):
    """Mapping for Person table"""
    __tablename__ = 'person'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)


class Person_Alias(Base):
    """Mapping for Person_Alias table"""
    __tablename__ = 'person_alias'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey(Person.id), doc='Link to person', nullable=False)
    name = Column(Unicode(50), nullable=False)
    person = relationship(Person)


class Connection_Type(Base):
    """Mapping for Connection_Type table"""
    __tablename__ = 'connection_type'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)


class Work_Person(Base):
    """Mapping for Work_Person table"""
    __tablename__ = 'work_person'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    work_id = Column(Integer, ForeignKey(Work.id), nullable=False)
    person_id = Column(Integer, ForeignKey(Person.id), nullable=False)
    action_id = Column(Integer, ForeignKey(Action.id))
    title_id = Column(Integer, ForeignKey(Title.id))
    place_id = Column(Integer, ForeignKey(Place.id))
    time = Column(Unicode(50))


class Connection(Base):
    """Mapping for Connection table"""
    __tablename__ = 'connection'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    work_person_id = Column(Integer, ForeignKey(Work_Person.id), nullable=False)
    connect_type_id = Column(Integer, ForeignKey(Connection_Type.id), nullable=False)
    person_id = Column(Integer, ForeignKey(Person.id), nullable=False)
    title_id = Column(Integer, ForeignKey(Title.id))
