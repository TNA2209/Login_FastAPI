from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    hashed_password: str

class User(UserBase):
    id: str
    role:str
    class Config:
        orm_mode = True

class UserCreate(UserBase):
    pass