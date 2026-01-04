from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from .user import UserResponseSchema

class NoteCreate(BaseModel):
    """Schema for creating a note"""
    title: str = Field(..., min_length=1, max_length=200, description="Title of the note")
    content: Optional[str] = Field(None, description="Content of the note")
    
    model_config = ConfigDict(from_attributes=True)

class NoteUpdate(BaseModel):
    """Schema for updating a note (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class NoteSchema(BaseModel):
    """Schema for returning note data"""
    id: int
    user_id: int
    title: str
    content: Optional[str]
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponseSchema] = None
    
    model_config = ConfigDict(from_attributes=True)