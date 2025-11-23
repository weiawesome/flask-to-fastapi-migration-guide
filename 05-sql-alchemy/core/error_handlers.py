"""
Error Handlers
錯誤處理器 - 統一處理各種例外
類似 Flask 的 @app.errorhandler()
"""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from middleware.request_id_middleware import get_request_id

# 使用統一的 logger 名稱，確保日誌會寫入檔案
logger = logging.getLogger("fastapi_app")


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    處理 HTTP 例外
    
    相當於 Flask 的：
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        ...
    """
    request_id = get_request_id()
    
    logger.error(
        f"HTTP Exception: {exc.status_code} - {exc.detail} "
        f"(Request ID: {request_id})"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "status_code": exc.status_code,
                "message": exc.detail,
                "request_id": request_id
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    處理 Pydantic 驗證例外
    當請求資料不符合 Pydantic 模型時觸發
    """
    request_id = get_request_id()
    
    # 格式化錯誤訊息
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Validation Error: {errors} (Request ID: {request_id})"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "status_code": 422,
                "message": "Validation failed",
                "details": errors,
                "request_id": request_id
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    處理未預期的例外
    捕獲所有未處理的例外，避免應用崩潰
    
    相當於 Flask 的：
    @app.errorhandler(Exception)
    def handle_exception(e):
        ...
    """
    request_id = get_request_id()
    
    logger.error(
        f"Unexpected Error: {type(exc).__name__}: {str(exc)} "
        f"(Request ID: {request_id})",
        exc_info=True  # 記錄完整的 traceback
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "status_code": 500,
                "message": "Internal server error",
                "type": type(exc).__name__,
                "request_id": request_id
            }
        }
    )

