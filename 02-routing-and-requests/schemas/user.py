"""
User Schemas
使用 Pydantic 定義使用者資料模型
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """使用者基礎模型 - 共用欄位"""
    username: str = Field(..., min_length=3, max_length=50, description="使用者名稱")
    email: EmailStr = Field(..., description="電子郵件")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")


class UserCreate(UserBase):
    """建立使用者的請求模型"""
    password: str = Field(..., min_length=6, description="密碼")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "password": "secret123"
            }
        }


class UserUpdate(BaseModel):
    """更新使用者的請求模型 - 所有欄位都是可選的"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)


class UserResponse(UserBase):
    """使用者回應模型 - 不包含密碼"""
    id: int = Field(..., description="使用者 ID")
    created_at: datetime = Field(..., description="建立時間")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "created_at": "2024-01-01T00:00:00"
            }
        }
