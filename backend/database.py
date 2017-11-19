"""This module manages the application-level database."""
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Database configuration
engine = create_engine('sqlite:///projects.db', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
BaseModel = declarative_base()
BaseModel.query = db_session.query_property()


def init_db():
    """Import all modules here that might define models so that they will be registered properly on the metadata."""
    import projects
    BaseModel.metadata.create_all(bind=engine)
