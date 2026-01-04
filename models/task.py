from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import BaseModel

class TaskModel(BaseModel):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False) 
    description = Column(String(255), nullable=False)  
    due_date = Column(DateTime, nullable=True)  
    is_completed = Column(Boolean, default=False) 
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc)) 
    
    # Foreign key linking to users table
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    user = relationship('UserModel')