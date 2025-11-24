"""
Cache Manager with Redis
Redis 快取管理器 - 解決快取雪崩、穿透、擊穿問題
"""
import redis
import json
import random
import threading
import time
import os
from typing import Optional, Any, Callable
from .bloom_filter import BloomFilter


class CacheManager:
    """
    Redis 快取管理器
    解決三大快取問題：
    1. 快取雪崩 (Cache Avalanche) - 隨機過期時間
    2. 快取穿透 (Cache Penetration) - 布隆過濾器 + 空值快取
    3. 快取擊穿 (Cache Breakdown) - 互斥鎖
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        初始化快取管理器
        
        Args:
            redis_url: Redis 連接 URL，預設從環境變數讀取
        """
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        # 使用連接池優化性能
        self.redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            max_connections=50,  # 連接池大小
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={},
        )
        
        # 互斥鎖字典（用於快取擊穿防護）
        self._locks: dict[str, threading.Lock] = {}
        self._lock_dict_lock = threading.Lock()
        
        # 布隆過濾器（用於快取穿透防護）
        self.bloom_filter = BloomFilter(
            redis_client=self.redis_client,
            key="bloom:todo_keys",
            capacity=10000,
            error_rate=0.01
        )
        
        # 預設過期時間（秒）
        self.default_ttl = 3600  # 1 小時
        self.null_ttl = 300  # 空值快取 5 分鐘
    
    def _get_lock(self, key: str) -> threading.Lock:
        """
        獲取或創建互斥鎖（用於快取擊穿防護）
        
        Args:
            key: 快取 key
            
        Returns:
            threading.Lock: 互斥鎖
        """
        with self._lock_dict_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]
    
    def _get_random_ttl(self, base_ttl: int, random_range: int = 300) -> int:
        """
        獲取隨機過期時間（解決快取雪崩）
        
        Args:
            base_ttl: 基礎過期時間（秒）
            random_range: 隨機範圍（秒），預設 300 秒（5 分鐘）
            
        Returns:
            int: 隨機過期時間
        """
        return base_ttl + random.randint(0, random_range)
    
    def get(self, key: str) -> Optional[Any]:
        """
        從快取獲取資料
        
        Args:
            key: 快取 key
            
        Returns:
            Optional[Any]: 快取的值，如果不存在返回 None
        """
        value = self.redis_client.get(key)
        if value is None:
            return None
        
        # 檢查是否為空值標記
        if value == "__NULL__":
            return None
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        use_random_ttl: bool = True
    ) -> bool:
        """
        設置快取
        
        Args:
            key: 快取 key
            value: 要快取的值
            ttl: 過期時間（秒），如果為 None 使用預設值
            use_random_ttl: 是否使用隨機 TTL（解決快取雪崩）
            
        Returns:
            bool: 是否設置成功
        """
        if ttl is None:
            ttl = self.default_ttl
        
        # 使用隨機 TTL 解決快取雪崩
        if use_random_ttl:
            ttl = self._get_random_ttl(ttl)
        
        # 序列化值
        if isinstance(value, str):
            serialized_value = value
        else:
            serialized_value = json.dumps(value)
        
        return self.redis_client.setex(key, ttl, serialized_value)
    
    def set_null(self, key: str, ttl: Optional[int] = None) -> bool:
        """
        設置空值快取（解決快取穿透）
        
        Args:
            key: 快取 key
            ttl: 過期時間（秒），預設使用 null_ttl
            
        Returns:
            bool: 是否設置成功
        """
        if ttl is None:
            ttl = self.null_ttl
        
        return self.redis_client.setex(key, ttl, "__NULL__")
    
    def delete(self, key: str) -> bool:
        """
        刪除快取
        
        Args:
            key: 快取 key
            
        Returns:
            bool: 是否刪除成功
        """
        return bool(self.redis_client.delete(key))
    
    def delete_pattern(self, pattern: str) -> int:
        """
        根據模式刪除多個快取
        
        Args:
            pattern: Redis key 模式（例如 "todos:user:*"）
            
        Returns:
            int: 刪除的 key 數量
        """
        keys = self.redis_client.keys(pattern)
        if keys:
            return self.redis_client.delete(*keys)
        return 0
    
    def get_or_set(
        self,
        key: str,
        fetch_func: Callable[[], Any],
        ttl: Optional[int] = None,
        check_bloom: bool = True
    ) -> Any:
        """
        獲取快取，如果不存在則調用函數獲取並設置快取
        完整解決快取雪崩、穿透、擊穿問題
        
        Args:
            key: 快取 key
            fetch_func: 獲取資料的函數（如果快取不存在時調用）
            ttl: 過期時間（秒）
            check_bloom: 是否檢查布隆過濾器（解決快取穿透）
            
        Returns:
            Any: 快取或獲取的資料
        """
        # 1. 先嘗試從快取獲取
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        # 2. 檢查布隆過濾器（解決快取穿透）
        if check_bloom and not self.bloom_filter.exists(key):
            # 布隆過濾器中不存在，表示這個 key 一定不存在
            # 設置空值快取，避免重複查詢資料庫
            self.set_null(key)
            return None
        
        # 3. 使用互斥鎖防止快取擊穿（本地鎖，性能優異）
        lock = self._get_lock(key)
        with lock:
            # 雙重檢查：獲取鎖後再次檢查快取
            cached_value = self.get(key)
            if cached_value is not None:
                return cached_value
            
            # 4. 從資料源獲取資料
            try:
                value = fetch_func()
                
                # 對於列表類型，空列表 [] 是有效結果，不應該設置空值快取
                # 只有當 value 是 None 時才設置空值快取
                if value is None:
                    # 資料不存在，設置空值快取並添加到布隆過濾器
                    self.set_null(key)
                    if check_bloom:
                        self.bloom_filter.add(key)
                    return None
                else:
                    # 資料存在（包括空列表），設置快取並添加到布隆過濾器
                    self.set(key, value, ttl=ttl)
                    if check_bloom:
                        self.bloom_filter.add(key)
                    return value
            except Exception as e:
                # 獲取資料失敗，不設置快取
                raise e
    
    def invalidate_user_todos(self, user_id: int) -> None:
        """
        使某個用戶的所有 TODO 快取失效
        
        Args:
            user_id: 用戶 ID
        """
        # 清除用戶的所有 todos 列表快取
        self.delete_pattern(f"todos:user:{user_id}")
        # 注意：不清除單個 todo 快取，因為其他用戶可能也在使用
    
    def invalidate_todo(self, todo_id: int) -> None:
        """
        使某個 TODO 的快取失效
        
        Args:
            todo_id: TODO ID
        """
        # 清除單個 todo 的快取
        self.delete(f"todo:{todo_id}")
        # 注意：布隆過濾器不需要清除，因為它只判斷是否存在，不存儲具體值

