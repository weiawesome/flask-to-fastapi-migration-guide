"""
Password Utils
密碼工具函數 - 使用 bcrypt 進行密碼加密和驗證
"""
import bcrypt


def hash_password(password: str) -> str:
    """
    使用 bcrypt 加密密碼
    
    Args:
        password: 明文密碼
    
    Returns:
        str: 加密後的密碼哈希
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    驗證密碼是否匹配
    
    Args:
        plain_password: 明文密碼
        hashed_password: 加密後的密碼哈希
    
    Returns:
        bool: 是否匹配
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

