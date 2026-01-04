from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from .user import UserResponseSchema

class DailyGoalCreate(BaseModel):
    """Schema for creating a new daily goal"""
    title: str = Field(..., min_length=1, max_length=100, description="Title of the daily goal")
    description: str = Field(..., max_length=500, description="Description of the daily goal")
    goal_date: date = Field(..., description="Date for the daily goal")
    
    model_config = ConfigDict(
        from_attributes=True, 
        json_schema_extra={  
            "example": {
                "title": "Complete project report",
                "description": "Finish writing the project report",
                "goal_date": "2024-01-15"
            }
        }
    )

class DailyGoalUpdate(BaseModel):
    """Schema for updating a daily goal (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    goal_date: Optional[date] = None
    is_completed: Optional[bool] = Field(None, description="Mark goal as completed or not")
    
    model_config = ConfigDict(from_attributes=True)

class DailyGoalSchema(BaseModel):
    """Schema for returning daily goal data"""
    id: int
    title: str
    description: str
    goal_date: date
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    user: UserResponseSchema
    
    model_config = ConfigDict(from_attributes=True)