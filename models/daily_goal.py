from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from models.base import BaseModel
from datetime import date


class DailyGoalModel(BaseModel):
    __tablename__ = "daily_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)  
    goal_date = Column(Date, nullable=False, default=date.today)
    is_completed = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationship 
    user = relationship('UserModel')
    
    def __repr__(self):
        return f"<DailyGoal(id={self.id}, title='{self.title}', date={self.goal_date})>"