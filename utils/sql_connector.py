from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL=os.environ.get("DB_URL")

Base = declarative_base()

engine = create_engine(DB_URL, echo=True)

Session = sessionmaker(bind=engine)

def get_session():
    return Session()