from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .user import UserResponseSchema

class TaskCreate(BaseModel):
    """Schema for creating a new task"""
    title: str = Field(..., min_length=1, max_length=200, description="Title of the task")
    description: str = Field(..., max_length=255, description="Description of the task")
    due_date: Optional[datetime] = Field(None, description="Due date for the task (optional)")

class TaskUpdate(BaseModel):
    """Schema for updating a task (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=255)
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None

class TaskSchema(BaseModel):
    """Schema for returning task data"""
    id: int
    title: str
    description: str
    due_date: Optional[datetime]
    is_completed: bool
    created_at: datetime
    user: UserResponseSchema

    class Config:
        from_attributes = True