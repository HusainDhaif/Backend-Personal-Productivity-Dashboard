from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from .user import UserResponseSchema

class HabitCreate(BaseModel):
    """Schema for creating a new habit"""
    title: str = Field(..., min_length=1, max_length=200, description="Title of the habit")
    description: Optional[str] = Field(None, max_length=500, description="Description of the habit")

class HabitUpdate(BaseModel):
    """Schema for updating a habit (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_completed: Optional[bool] = Field(None, description="Mark habit as completed or not")

class HabitSchema(BaseModel):
    """Schema for returning habit data"""
    id: int 
    user_id: int
    title: str
    description: Optional[str]
    completed_at: Optional[datetime]
    is_completed: bool
    created_at: datetime
    
    # Include related data
    user: Optional[UserResponseSchema] = None

    class Config:
        from_attributes = True

class HabitWithDetails(HabitSchema):
    """Schema with all details including user"""
    user: UserResponseSchema

class HabitStats(BaseModel):
    """Schema for habit statistics"""
    total_habits: int
    completed_habits: int
    incomplete_habits: int