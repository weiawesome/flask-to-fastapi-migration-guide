"""
Core 模組測試
測試依賴注入和認證邏輯
"""
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from core.dependencies import get_current_user, get_current_user_optional
from core import get_current_user as imported_get_current_user


class TestGetCurrentUser:
    """測試 get_current_user 函數"""
    
    def test_get_current_user_valid_token(self):
        """測試有效的 token"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid-token"
        )
        
        user = get_current_user(credentials)
        
        assert user["user_id"] == 1
        assert user["username"] == "test_user"
    
    def test_get_current_user_admin_token(self):
        """測試管理員 token"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="admin-token"
        )
        
        user = get_current_user(credentials)
        
        assert user["user_id"] == 2
        assert user["username"] == "admin"
        assert user["role"] == "admin"
    
    def test_get_current_user_invalid_token(self):
        """測試無效的 token"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid-token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail
    
    def test_get_current_user_empty_token(self):
        """測試空 token"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=""
        )
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials)
        
        assert exc_info.value.status_code == 401


class TestGetCurrentUserOptional:
    """測試 get_current_user_optional 函數"""
    
    def test_get_current_user_optional_no_credentials(self):
        """測試沒有憑證時返回 None"""
        result = get_current_user_optional(None)
        
        assert result is None
    
    def test_get_current_user_optional_valid_token(self):
        """測試有效的 token"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid-token"
        )
        
        user = get_current_user_optional(credentials)
        
        assert user is not None
        assert user["user_id"] == 1
        assert user["username"] == "test_user"
    
    def test_get_current_user_optional_invalid_token(self):
        """測試無效的 token 時返回 None"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid-token"
        )
        
        result = get_current_user_optional(credentials)
        
        # 無效 token 時應該返回 None（不拋出異常）
        assert result is None


class TestCoreModule:
    """測試 core 模組導入"""
    
    def test_core_import(self):
        """測試 core 模組可以正常導入"""
        # 測試導入的函數是否可用
        assert callable(imported_get_current_user)
        assert imported_get_current_user == get_current_user
    
    def test_core_module_has_get_current_user(self):
        """測試 core 模組導出 get_current_user"""
        from core import __all__
        
        assert "get_current_user" in __all__

