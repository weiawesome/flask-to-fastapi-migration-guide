"""
Error Handlers
錯誤處理器
"""
from flask import jsonify
from .exceptions import (
    NotFoundException,
    UnauthorizedException,
    BadRequestException,
    ValidationException
)


def register_error_handlers(app):
    """
    註冊錯誤處理器
    
    Args:
        app: Flask 應用實例
    """
    
    @app.errorhandler(NotFoundException)
    def handle_not_found(error):
        return jsonify({"error": error.message}), 404
    
    @app.errorhandler(UnauthorizedException)
    def handle_unauthorized(error):
        return jsonify({"error": error.message}), 401
    
    @app.errorhandler(BadRequestException)
    def handle_bad_request(error):
        return jsonify({"error": error.message}), 400
    
    @app.errorhandler(ValidationException)
    def handle_validation(error):
        return jsonify({"error": error.message}), 422
    
    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def handle_500(e):
        return jsonify({"error": "Internal server error"}), 500

