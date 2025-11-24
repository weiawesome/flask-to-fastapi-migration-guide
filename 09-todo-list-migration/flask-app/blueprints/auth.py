"""
Auth Blueprint
認證相關路由
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from database import get_db
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from schemas.auth import RegisterRequest, LoginRequest
from utils.cache import CacheManager
from core.exceptions import BadRequestException, UnauthorizedException

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')
cache_manager = CacheManager()


@auth_bp.route('/register', methods=['POST'])
def register():
    """用戶註冊"""
    try:
        # 驗證請求資料
        data = request.get_json()
        register_data = RegisterRequest(**data)
        
        # 獲取資料庫 session
        db = next(get_db())
        try:
            user_repo = UserRepository(db)
            auth_service = AuthService(user_repo)
            
            result = auth_service.register(
                username=register_data.username,
                email=register_data.email,
                password=register_data.password
            )
            
            return jsonify(result), 201
        finally:
            db.close()
    except ValidationError as e:
        return jsonify({"error": str(e)}), 422
    except BadRequestException as e:
        return jsonify({"error": e.message}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """用戶登入"""
    try:
        # 驗證請求資料
        data = request.get_json()
        login_data = LoginRequest(**data)
        
        # 獲取資料庫 session
        db = next(get_db())
        try:
            user_repo = UserRepository(db)
            auth_service = AuthService(user_repo)
            
            result = auth_service.login(
                email=login_data.email,
                password=login_data.password
            )
            
            return jsonify(result), 200
        finally:
            db.close()
    except ValidationError as e:
        return jsonify({"error": str(e)}), 422
    except UnauthorizedException as e:
        return jsonify({"error": e.message}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用戶登出（將 token 加入黑名單）"""
    try:
        # 獲取 Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Missing authorization header"}), 401
        
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                return jsonify({"error": "Invalid authorization scheme"}), 401
        except ValueError:
            return jsonify({"error": "Invalid authorization header format"}), 401
        
        # 將 token 加入黑名單（設置 30 分鐘過期，與 JWT token 過期時間一致）
        cache_manager.set(f"jwt:blacklist:{token}", True, ttl=1800)
        
        return jsonify({"message": "Logged out successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

