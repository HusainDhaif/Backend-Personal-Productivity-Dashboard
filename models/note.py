from sqlalchemy import Column, Integer, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from models.base import BaseModel

class NoteModel(BaseModel):
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(200), nullable=False) 
    content = Column(Text, nullable=True) 
    
    # Relationships
    user = relationship('UserModel', backref='notes')
    
    def __repr__(self):
        return f"<Note(user_id={self.user_id}, title='{self.title}')>"