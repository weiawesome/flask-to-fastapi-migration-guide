"""
User Service - 用戶服務層
支持依賴注入其他 Service，便於在測試中 Mock
"""
from typing import Optional
from fastapi import Depends

from repositories.user_repository import UserRepository, User, get_user_repository


class NotificationService:
    """通知服務（示例：可被 UserService 依賴）"""
    
    async def send_notification(self, message: str) -> None:
        """發送通知（示例方法）"""
        # 實際應用中會發送郵件、短信等
        print(f"Notification: {message}")


def get_notification_service() -> NotificationService:
    """獲取 NotificationService 實例（依賴注入）"""
    return NotificationService()


class UserService:
    """用戶服務層（可依賴其他 Service）"""
    
    def __init__(
        self,
        user_repo: UserRepository,
        notification_service: Optional[NotificationService] = None
    ):
        self.user_repo = user_repo
        self.notification_service = notification_service
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """
        獲取用戶
        
        如果配置了 notification_service，會在獲取用戶時發送通知
        這樣可以在測試中 Mock notification_service 來驗證行為
        """
        user = self.user_repo.get_by_id(user_id)
        
        # 如果用戶存在且配置了通知服務，發送通知
        if user and self.notification_service:
            await self.notification_service.send_notification(
                f"User {user_id} ({user.username}) was accessed"
            )
        
        return user


# 依賴注入
def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
    notification_service: Optional[NotificationService] = Depends(get_notification_service)
) -> UserService:
    """獲取 UserService 實例（依賴注入）"""
    return UserService(user_repo, notification_service)