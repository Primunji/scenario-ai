from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL=os.environ.get("DB_URL")

Base = declarative_base()

engine = create_engine(DB_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 세션을 반환하는 의존성 함수
def get_session():
    db = SessionLocal()
    try:
        yield db  # 세션을 사용한 후, FastAPI가 자동으로 세션을 닫습니다.
    finally:
        db.close()