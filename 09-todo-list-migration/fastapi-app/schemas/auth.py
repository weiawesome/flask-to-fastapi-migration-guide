"""
Auth Schemas
認證相關的資料結構
"""
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """註冊請求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    """登入請求"""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """認證回應"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str

