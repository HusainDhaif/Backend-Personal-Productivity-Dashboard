from pydantic import BaseModel, Field
from typing import Optional
from models.user import UserRole  

class UserSchema(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[str] = Field(default="CUSTOMER")  # Accept string, will be converted in controller
    
    class Config:
        from_attributes = True

class UserResponseSchema(BaseModel):
    id: int
    username: str
    email: str
    role: Optional[UserRole] = Field(default=UserRole.CUSTOMER)
    
    class Config:
        from_attributes = True  
        use_enum_values = True

class UserLogin(BaseModel):
    username: str
    password: str

class UserToken(BaseModel):
    token: str
    message: str
    role: UserRole  
    
    class Config:
        from_attributes = True 
        use_enum_values = True