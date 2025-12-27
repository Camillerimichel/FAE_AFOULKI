from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    fullname = Column(String(255), nullable=True)
    reset_token_hash = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)

    roles = relationship("Role", secondary="user_roles", back_populates="users")
