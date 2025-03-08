from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Scenario(Base):
    __tablename__ = "scenario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    profile_url = Column(String(255), nullable=False)
    actor_id = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=False)
    assistant_id = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Scenario(id={self.id}, name={self.name}, actor_id={self.actor_id})>"
