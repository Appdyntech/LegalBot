# backend/app/models/chat_history.py
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from . import Base

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(100), unique=True, nullable=False)
    session_id = Column(String(100))
    user_name = Column(String(100))
    question = Column(Text)
    answer = Column(Text)
    confidence_score = Column(String(50))
    model_used = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
