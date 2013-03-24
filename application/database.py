from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from models import Base

from settings import DB_CONNECT_STRING

engine = create_engine(DB_CONNECT_STRING, convert_unicode=True)
Session = scoped_session(sessionmaker(bind=engine,
                                      autocommit=False,
                                      autoflush=False,))
Base.query = Session.query_property()


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata. Otherwise
    # you will have to import them first before calling init_db()
    import models
    # Session.begin()
    Base.metadata.create_all(bind=engine)
    Session.commit()
