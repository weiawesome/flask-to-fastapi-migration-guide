"""
User Schemas
使用 Pydantic 定義使用者資料模型
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class AuthBase(BaseModel):
    """使用者基礎模型 - 共用欄位"""
    email: EmailStr = Field(..., description="電子郵件")
    password: str = Field(..., min_length=6, description="密碼")


class AuthCreate(AuthBase):
    """建立使用者的請求模型"""

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "secret123"
            }
        }


class AuthLogin(AuthBase):
    """登入請求模型"""
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "secret123"
            }
        }

class AuthMe(BaseModel):
    """使用者回應模型 - 當前使用者資訊"""
    id: int = Field(..., description="使用者 ID")
    email: EmailStr = Field(..., description="電子郵件")
    created_at: datetime = Field(..., description="建立時間")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "john@example.com",
                "created_at": "2024-01-01T00:00:00"
            }
        }

class AuthResponse(BaseModel):
    """登入/註冊回應模型"""
    access_token: str = Field(..., description="存取權杖")
    token_type: str = Field(default="Bearer", description="權杖類型")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                "token_type": "Bearer"
            }
        }