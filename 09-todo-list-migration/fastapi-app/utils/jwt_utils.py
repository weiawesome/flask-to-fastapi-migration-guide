"""
JWT Utils
JWT 工具函數 - 負責創建和驗證 JWT token
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt


# JWT 設定
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(
    data: Dict,
    expires_delta: Optional[timedelta] = None,
    secret_key: Optional[str] = None
) -> str:
    """
    創建 JWT access token
    
    Args:
        data: 要編碼到 token 中的資料（通常是 user_id, email 等）
        expires_delta: token 過期時間（可選，預設為 ACCESS_TOKEN_EXPIRE_MINUTES）
        secret_key: 密鑰（可選，預設使用 SECRET_KEY）
    
    Returns:
        str: JWT token 字串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    key = secret_key or SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, key, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(
    token: str,
    secret_key: Optional[str] = None
) -> Dict:
    """
    驗證 JWT token
    
    Args:
        token: JWT token 字串
        secret_key: 密鑰（可選，預設使用 SECRET_KEY）
    
    Returns:
        dict: 解碼後的 token 資料
    
    Raises:
        ValueError: token 無效或過期
    """
    try:
        key = secret_key or SECRET_KEY
        payload = jwt.decode(token, key, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")


def create_token_for_user(user_id: int, email: str) -> str:
    """
    為使用者創建 JWT token
    
    Args:
        user_id: 使用者 ID
        email: 使用者電子郵件
    
    Returns:
        str: JWT token 字串
    """
    token_data = {"sub": str(user_id), "email": email}
    return create_access_token(data=token_data)

