from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import BaseModel

class HabitModel(BaseModel):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True) 
    
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)

    # Relationships
    user = relationship('UserModel')