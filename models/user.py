from sqlalchemy import Column, Integer, String, Enum
from .base import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
import jwt
from config.environment import secret
from sqlalchemy.orm import relationship
import enum

# Define UserRole enum
class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserModel(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=True)
    # Use String for role to match VARCHAR(50) in database, with default 'CUSTOMER'
    role = Column(String(50), default='CUSTOMER', nullable=False, server_default='CUSTOMER')  
    
    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)
    
    def generate_token(self):
        # Get role value, defaulting to 'CUSTOMER' if role is None
        role_value = self.role if self.role else 'CUSTOMER'
        
        payload = {
            "exp": datetime.now(timezone.utc) + timedelta(days=1),
            "iat": datetime.now(timezone.utc),
            "sub": str(self.id),
            "role": role_value
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        return token
    
    def is_admin(self):
        return self.role == UserRole.ADMIN.value or self.role == 'ADMIN'
    
    def is_customer(self):
        return self.role == UserRole.CUSTOMER.value or self.role == 'CUSTOMER'