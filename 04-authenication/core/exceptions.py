"""
Custom Exceptions
自訂例外 - 方便統一處理錯誤
"""
from fastapi import HTTPException, status


class UserNotFoundException(HTTPException):
    """使用者不存在例外"""
    def __init__(self, user_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )


class UserAlreadyExistsException(HTTPException):
    """使用者已存在例外"""
    def __init__(self, username: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{username}' already exists"
        )


class ValidationException(HTTPException):
    """資料驗證例外"""
    def __init__(self, field: str, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "field": field,
                "message": message
            }
        )


class DatabaseException(HTTPException):
    """資料庫例外"""
    def __init__(self, message: str = "Database error occurred"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )


class InvalidCredentialsException(HTTPException):
    """無效憑證例外"""
    def __init__(self, identifier: str = "credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid credentials for {identifier}",
            headers={"WWW-Authenticate": "Bearer"}
        )


class TokenExpiredException(HTTPException):
    """Token 過期例外"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )


class InvalidTokenException(HTTPException):
    """無效 Token 例外"""
    def __init__(self, detail: str = "Invalid token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

