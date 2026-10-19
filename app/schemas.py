from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: int | None = None

class RefreshRequest(BaseModel):
    refresh_token: str

class ListOfUsersResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    users: list[UserResponse]