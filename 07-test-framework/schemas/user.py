"""
User Schema - Pydantic 模型
"""
from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """用戶回應模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: str
