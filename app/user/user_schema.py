from pydantic import BaseModel, EmailStr

class User(BaseModel):
    email: EmailStr
    password: str
    username: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: EmailStr
    new_password: str

class UserDeleteRequest(BaseModel):
    email: EmailStr

class MessageResponse(BaseModel):
    message: str

