from sqlalchemy import String, Column, ForeignKey
from sqlalchemy.orm import relationship
from db import Base

class User(Base):
    __tablename__ = "user"
    id = Column(String(100), primary_key=True, index=True,nullable=False)
    username = Column(String(50), unique=True, index=True,nullable=False)
    hashed_password = Column(String(128),nullable=False)
    role = Column(String(20), nullable = False)