"""
Custom Exceptions
自訂例外 - 方便統一處理錯誤
"""
from fastapi import HTTPException, status


class CustomException(HTTPException):
    """自訂例外基類"""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(HTTPException):
    """資源不存在例外"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with identifier '{identifier}' not found"
        )


class ValidationError(HTTPException):
    """資料驗證例外"""
    def __init__(self, field: str, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "field": field,
                "message": message
            }
        )


class DatabaseError(HTTPException):
    """資料庫例外"""
    def __init__(self, message: str = "Database error occurred"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

