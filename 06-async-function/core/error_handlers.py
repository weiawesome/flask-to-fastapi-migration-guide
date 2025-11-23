"""
Error Handlers
錯誤處理器 - 統一處理各種例外
"""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("fastapi_app")


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """處理 HTTP 例外"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "status_code": exc.status_code,
                "message": exc.detail
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """處理 Pydantic 驗證例外"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation Error: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "status_code": 422,
                "message": "Validation failed",
                "details": errors
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """處理未預期的例外"""
    logger.error(
        f"Unexpected Error: {type(exc).__name__}: {str(exc)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "status_code": 500,
                "message": "Internal server error",
                "type": type(exc).__name__
            }
        }
    )

