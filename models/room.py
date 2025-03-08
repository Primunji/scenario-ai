from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Room(Base):
    __tablename__ = 'room'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String, nullable=False)
    scenario_id = Column(Integer, nullable=False)
    user_id = Column('user_id', Integer, nullable=False)
    name = Column(String, nullable=False)
    content = Column(String, nullable=False)
    profile_url = Column(String, nullable=False)
    recent_message = Column(String, nullable=True)
    last_message = Column(Date, nullable=False, default=datetime.utcnow)
    created_at = Column(Date, nullable=False, default=datetime.utcnow)
