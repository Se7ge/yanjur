# -*- coding: utf-8 -*-

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Unicode, UnicodeText, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class Work_Categories(Base):
    """Mapping for Work_Categories table"""
    __tablename__ = 'work_categories'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    code = Column(UnicodeText, nullable=True)

    def __unicode__(self):
        return self.name


class Work(Base):
    """Mapping for Work table"""
    __tablename__ = 'work'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey(Work_Categories.id), doc='Link to category', nullable=False)
    number = Column(String(10), nullable=False)
    name = Column(Unicode(255), nullable=False)
    location = Column(Unicode(50))
    colophon = Column(UnicodeText)
    concordance = Column(Unicode(50))
    #TODO: many-to-many
    concordance_work_id = Column(Integer, ForeignKey('work.id'), doc='Link to work', nullable=True)
    category = relationship(Work_Categories)


class Action(Base):
    """Mapping for Action table"""
    __tablename__ = 'action'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)


class Place(Base):
    """Mapping for Place table"""
    __tablename__ = 'place'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)


class Title(Base):
    """Mapping for Title table"""
    __tablename__ = 'title'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)


class Person(Base):
    """Mapping for Person table"""
    __tablename__ = 'person'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)

    def __unicode__(self):
        return self.name


class Person_Alias(Base):
    """Mapping for Person_Alias table"""
    __tablename__ = 'person_alias'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey(Person.id), doc='Link to person')
    name = Column(Unicode(50), nullable=False)
    person = relationship(Person)


class Connection_Type(Base):
    """Mapping for Connection_Type table"""
    __tablename__ = 'connection_type'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)


class Work_Time(Base):
    """Mapping for Work_Time table"""
    __tablename__ = 'work_time'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)


class Work_Person(Base):
    """Mapping for Work_Person table"""
    __tablename__ = 'work_person'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    work_id = Column(Integer, ForeignKey(Work.id), nullable=False)
    person_id = Column(Integer, ForeignKey(Person.id), nullable=False)
    place_id = Column(Integer, ForeignKey(Place.id))
    time_id = Column(Integer, ForeignKey(Work_Time.id))

    work = relationship(Work)
    titles = relationship(Title, secondary='work_person_titles', backref='works')
    actions = relationship(Action, secondary='work_person_actions', backref='works')
    times = relationship(Work_Time, backref='works')
    places = relationship(Place, backref='works')


class Work_Person_Titles(Base):
    """Mapping for Work_Person_Titles table"""
    __tablename__ = 'work_person_titles'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    work_person_id = Column(Integer, ForeignKey(Work_Person.id), primary_key=True)
    title_id = Column(Integer, ForeignKey(Title.id), primary_key=True)


class Work_Person_Actions(Base):
    """Mapping for Work_Person_Actions table"""
    __tablename__ = 'work_person_actions'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    work_person_id = Column(Integer, ForeignKey(Work_Person.id), primary_key=True)
    action_id = Column(Integer, ForeignKey(Action.id), primary_key=True)


class Connection(Base):
    """Mapping for Connection table"""
    __tablename__ = 'connection'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    work_person_id = Column(Integer, ForeignKey(Work_Person.id), nullable=False)
    connect_type_id = Column(Integer, ForeignKey(Connection_Type.id), nullable=False)
    person_id = Column(Integer, ForeignKey(Person.id), nullable=False)


class Connection_Titles(Base):
    """Mapping for Work_Person_Titles table"""
    __tablename__ = 'connection_titles'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    connection_id = Column(Integer, ForeignKey(Connection.id), primary_key=True)
    title_id = Column(Integer, ForeignKey(Title.id), primary_key=True)


class Pages(Base):
    """Mapping for Pages table"""
    __tablename__ = 'pages'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    title = Column(Unicode(100), nullable=False)
    text = Column(UnicodeText)
    url = Column(Unicode(50), nullable=False)
