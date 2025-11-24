"""
Cache Manager with Redis (Async)
Redis 快取管理器 - 解決快取雪崩、穿透、擊穿問題 (異步版本)
"""
import redis.asyncio as aioredis
import json
import random
import asyncio
import os
from typing import Optional, Any, Callable, Awaitable
from .bloom_filter import BloomFilter


class CacheManager:
    """
    Redis 快取管理器 (異步版本)
    解決三大快取問題：
    1. 快取雪崩 (Cache Avalanche) - 隨機過期時間
    2. 快取穿透 (Cache Penetration) - 布隆過濾器 + 空值快取
    3. 快取擊穿 (Cache Breakdown) - 分散式鎖 (Redis SETNX)
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        初始化快取管理器
        
        Args:
            redis_url: Redis 連接 URL，預設從環境變數讀取
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client: Optional[aioredis.Redis] = None
        
        # 分散式鎖字典（用於快取擊穿防護）
        self._locks: dict[str, asyncio.Lock] = {}
        self._lock_dict_lock = asyncio.Lock()
        
        # 布隆過濾器（用於快取穿透防護）
        self.bloom_filter: Optional[BloomFilter] = None
        
        # 預設過期時間（秒）
        self.default_ttl = 3600  # 1 小時
        self.null_ttl = 300  # 空值快取 5 分鐘
        self.lock_ttl = 10  # 鎖過期時間 10 秒
    
    async def _get_redis(self) -> aioredis.Redis:
        """獲取 Redis 客戶端（使用連接池，優化性能）"""
        if self.redis_client is None:
            # 使用連接池優化性能
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=50,  # 連接池大小
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
            )
            self.bloom_filter = BloomFilter(
                redis_client=self.redis_client,
                key="bloom:todo_keys",
                capacity=10000,
                error_rate=0.01
            )
        return self.redis_client
    
    async def _get_lock(self, key: str) -> asyncio.Lock:
        """
        獲取或創建互斥鎖（用於快取擊穿防護）
        
        Args:
            key: 快取 key
            
        Returns:
            asyncio.Lock: 互斥鎖
        """
        async with self._lock_dict_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
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
    
    async def _acquire_distributed_lock(self, lock_key: str) -> bool:
        """
        獲取分散式鎖（Redis SETNX）
        
        Args:
            lock_key: 鎖的 key
            
        Returns:
            bool: 是否成功獲取鎖
        """
        # 優化：直接使用已建立的連接
        if self.redis_client is None:
            await self._get_redis()
        
        result = await self.redis_client.set(
            lock_key,
            "1",
            ex=self.lock_ttl,
            nx=True  # 只在 key 不存在時設置
        )
        return result is True
    
    async def _release_distributed_lock(self, lock_key: str) -> None:
        """
        釋放分散式鎖
        
        Args:
            lock_key: 鎖的 key
        """
        # 優化：直接使用已建立的連接
        if self.redis_client is None:
            await self._get_redis()
        
        await self.redis_client.delete(lock_key)
    
    async def get(self, key: str) -> Optional[Any]:
        """
        從快取獲取資料 (異步)
        
        Args:
            key: 快取 key
            
        Returns:
            Optional[Any]: 快取的值，如果不存在返回 None
        """
        # 優化：直接使用已建立的連接，避免每次調用 _get_redis()
        if self.redis_client is None:
            await self._get_redis()
        
        value = await self.redis_client.get(key)
        if value is None:
            return None
        
        # 檢查是否為空值標記
        if value == "__NULL__":
            return None
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        use_random_ttl: bool = True
    ) -> bool:
        """
        設置快取 (異步)
        
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
        
        # 優化：直接使用已建立的連接
        if self.redis_client is None:
            await self._get_redis()
        
        return await self.redis_client.setex(key, ttl, serialized_value)
    
    async def set_null(self, key: str, ttl: Optional[int] = None) -> bool:
        """
        設置空值快取（解決快取穿透）(異步)
        
        Args:
            key: 快取 key
            ttl: 過期時間（秒），預設使用 null_ttl
            
        Returns:
            bool: 是否設置成功
        """
        if ttl is None:
            ttl = self.null_ttl
        
        # 優化：直接使用已建立的連接
        if self.redis_client is None:
            await self._get_redis()
        
        return await self.redis_client.setex(key, ttl, "__NULL__")
    
    async def delete(self, key: str) -> bool:
        """
        刪除快取 (異步)
        
        Args:
            key: 快取 key
            
        Returns:
            bool: 是否刪除成功
        """
        # 優化：直接使用已建立的連接
        if self.redis_client is None:
            await self._get_redis()
        
        return bool(await self.redis_client.delete(key))
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        根據模式刪除多個快取 (異步)
        
        Args:
            pattern: Redis key 模式（例如 "todos:user:*"）
            
        Returns:
            int: 刪除的 key 數量
        """
        # 優化：直接使用已建立的連接
        if self.redis_client is None:
            await self._get_redis()
        
        keys = await self.redis_client.keys(pattern)
        if keys:
            return await self.redis_client.delete(*keys)
        return 0
    
    async def get_or_set(
        self,
        key: str,
        fetch_func: Callable[[], Awaitable[Any]],
        ttl: Optional[int] = None,
        check_bloom: bool = True
    ) -> Any:
        """
        獲取快取，如果不存在則調用函數獲取並設置快取 (異步)
        完整解決快取雪崩、穿透、擊穿問題
        
        Args:
            key: 快取 key
            fetch_func: 獲取資料的異步函數（如果快取不存在時調用）
            ttl: 過期時間（秒）
            check_bloom: 是否檢查布隆過濾器（解決快取穿透）
            
        Returns:
            Any: 快取或獲取的資料
        """
        # 1. 先嘗試從快取獲取
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # 2. 檢查布隆過濾器（解決快取穿透）
        if check_bloom and self.bloom_filter:
            exists = await self.bloom_filter.exists(key)
            if not exists:
                # 布隆過濾器中不存在，表示這個 key 一定不存在
                await self.set_null(key)
                return None
        
        # 3. 使用本地鎖防止快取擊穿（優化：在單實例環境下使用本地鎖更快）
        # 注意：如果有多個 FastAPI 實例，應該使用分散式鎖
        # 但在單實例情況下，本地鎖性能更好（類似 Flask）
        lock = await self._get_lock(key)
        async with lock:
            # 雙重檢查：獲取鎖後再次檢查快取
            cached_value = await self.get(key)
            if cached_value is not None:
                return cached_value
            
            # 4. 從資料源獲取資料
            value = await fetch_func()
            
            # 對於列表類型，空列表 [] 是有效結果，不應該設置空值快取
            # 只有當 value 是 None 時才設置空值快取
            if value is None:
                # 資料不存在，設置空值快取並添加到布隆過濾器
                await self.set_null(key)
                if self.bloom_filter:
                    await self.bloom_filter.add(key)
                return None
            else:
                # 資料存在（包括空列表），設置快取並添加到布隆過濾器
                await self.set(key, value, ttl=ttl)
                if self.bloom_filter:
                    await self.bloom_filter.add(key)
                return value
    
    async def invalidate_user_todos(self, user_id: int) -> None:
        """
        使某個用戶的所有 TODO 快取失效 (異步)
        
        Args:
            user_id: 用戶 ID
        """
        # 清除用戶的所有 todos 列表快取
        await self.delete_pattern(f"todos:user:{user_id}")
        # 注意：不清除單個 todo 快取，因為其他用戶可能也在使用
    
    async def invalidate_todo(self, todo_id: int) -> None:
        """
        使某個 TODO 的快取失效 (異步)
        
        Args:
            todo_id: TODO ID
        """
        # 清除單個 todo 的快取
        await self.delete(f"todo:{todo_id}")
        # 注意：布隆過濾器不需要清除，因為它只判斷是否存在，不存儲具體值

