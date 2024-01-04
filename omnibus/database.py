
#import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up database
DATABASE = 'sqlite:///databases/main.db'

engine = create_engine(DATABASE)
db = scoped_session(sessionmaker(bind=engine))