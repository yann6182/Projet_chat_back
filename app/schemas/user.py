from pydantic import BaseModel

class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    pass

class UserSchema(UserBase):
    id: int

    class Config:
        orm_mode = True
