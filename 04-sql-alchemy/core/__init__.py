"""
Core
核心模組 - 應用層級的基礎設施
包含例外定義和錯誤處理器
"""
from .exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
    ValidationException,
    DatabaseException,
    InvalidCredentialsException,
    TokenExpiredException,
    InvalidTokenException
)
from .error_handlers import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)

__all__ = [
    # Exceptions
    "UserNotFoundException",
    "UserAlreadyExistsException",
    "ValidationException",
    "DatabaseException",
    "InvalidCredentialsException",
    "TokenExpiredException",
    "InvalidTokenException",
    # Error Handlers
    "http_exception_handler",
    "validation_exception_handler",
    "general_exception_handler",
]

