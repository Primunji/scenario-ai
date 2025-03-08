from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    scenario_id = Column(Integer, nullable=False)
    thread_id = Column(String, nullable=False)
    assistant_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Call(id={self.id}, scenario_id={self.scenario_id}, thread_id={self.thread_id})>"
