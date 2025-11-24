"""
Custom Exceptions
自訂例外類別
"""


class NotFoundException(Exception):
    """資源不存在"""
    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(self.message)


class UnauthorizedException(Exception):
    """未授權"""
    def __init__(self, message: str = "Unauthorized"):
        self.message = message
        super().__init__(self.message)


class BadRequestException(Exception):
    """錯誤請求"""
    def __init__(self, message: str = "Bad request"):
        self.message = message
        super().__init__(self.message)


class ValidationException(Exception):
    """驗證錯誤"""
    def __init__(self, message: str = "Validation error"):
        self.message = message
        super().__init__(self.message)

