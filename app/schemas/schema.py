 
from pydantic import BaseModel

class ItemBase(BaseModel):
    name: str

class ItemCreate(ItemBase):
    pass

class ItemSchema(ItemBase):
    id: int
    
    class Config:
        orm_mode = True
class QuestionSchema(BaseModel):
    user_id: int
    question_text: str

    class Config:
        orm_mode = True
class ResponseSchema(BaseModel):
    question_id: int
    response_text: str

    class Config:
        orm_mode = True
