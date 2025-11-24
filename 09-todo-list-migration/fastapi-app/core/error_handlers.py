"""
Error Handlers
錯誤處理器
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from .exceptions import (
    NotFoundException,
    UnauthorizedException,
    BadRequestException,
    ValidationException
)


async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """處理 NotFoundException"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": exc.message}
    )


async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    """處理 UnauthorizedException"""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": exc.message}
    )


async def bad_request_exception_handler(request: Request, exc: BadRequestException):
    """處理 BadRequestException"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": exc.message}
    )


async def validation_exception_handler(request: Request, exc: ValidationException):
    """處理 ValidationException"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": exc.message}
    )

