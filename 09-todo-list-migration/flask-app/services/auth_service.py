"""
Auth Service
認證服務層
"""
from repositories.user_repository import UserRepository
from utils.password import hash_password, verify_password
from utils.jwt_utils import create_token_for_user
from core.exceptions import BadRequestException, UnauthorizedException


class AuthService:
    """認證服務層"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def register(self, username: str, email: str, password: str) -> dict:
        """
        註冊新用戶
        
        Args:
            username: 用戶名
            email: 電子郵件
            password: 密碼
            
        Returns:
            dict: 包含 access_token 和用戶資訊
            
        Raises:
            BadRequestException: 如果用戶名或郵件已存在
        """
        # 檢查用戶名是否已存在
        if self.user_repo.exists_by_username(username):
            raise BadRequestException("Username already exists")
        
        # 檢查郵件是否已存在
        if self.user_repo.exists_by_email(email):
            raise BadRequestException("Email already exists")
        
        # 加密密碼
        password_hash = hash_password(password)
        
        # 創建用戶
        user = self.user_repo.create(username, email, password_hash)
        
        # 生成 JWT token
        access_token = create_token_for_user(user.id, user.email)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email
        }
    
    def login(self, email: str, password: str) -> dict:
        """
        用戶登入
        
        Args:
            email: 電子郵件
            password: 密碼
            
        Returns:
            dict: 包含 access_token 和用戶資訊
            
        Raises:
            UnauthorizedException: 如果郵件或密碼錯誤
        """
        # 獲取用戶
        user = self.user_repo.get_by_email(email)
        if not user:
            raise UnauthorizedException("Invalid email or password")
        
        # 驗證密碼
        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")
        
        # 生成 JWT token
        access_token = create_token_for_user(user.id, user.email)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email
        }

