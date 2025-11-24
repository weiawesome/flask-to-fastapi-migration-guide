"""
Bloom Filter Implementation (Async)
布隆過濾器實作 - 用於快取穿透防護 (異步版本)
"""
import mmh3
import math
from typing import List
import redis.asyncio as aioredis


class BloomFilter:
    """
    布隆過濾器 - 用於快速判斷 key 是否存在 (異步版本)
    解決快取穿透問題：查詢不存在的資料時，先檢查布隆過濾器
    """
    
    def __init__(self, redis_client: aioredis.Redis, key: str, capacity: int = 10000, error_rate: float = 0.01):
        """
        初始化布隆過濾器
        
        Args:
            redis_client: Redis 客戶端 (aioredis)
            key: 布隆過濾器在 Redis 中的 key
            capacity: 預期容量（預期會插入的元素數量）
            error_rate: 誤判率（0-1 之間）
        """
        self.redis_client = redis_client
        self.key = key
        self.capacity = capacity
        self.error_rate = error_rate
        
        # 計算需要的位數和哈希函數數量
        self.bit_size = int(-capacity * math.log(error_rate) / (math.log(2) ** 2))
        self.hash_count = int(self.bit_size * math.log(2) / capacity)
        
        if self.hash_count < 1:
            self.hash_count = 1
    
    def _get_offsets(self, item: str) -> List[int]:
        """
        獲取 item 對應的所有位偏移量
        
        Args:
            item: 要檢查的元素
            
        Returns:
            List[int]: 位偏移量列表
        """
        offsets = []
        for i in range(self.hash_count):
            hash_value = mmh3.hash(item, i) % self.bit_size
            offsets.append(hash_value)
        return offsets
    
    async def add(self, item: str) -> None:
        """
        添加元素到布隆過濾器 (異步)
        
        Args:
            item: 要添加的元素
        """
        offsets = self._get_offsets(item)
        pipe = self.redis_client.pipeline()
        for offset in offsets:
            pipe.setbit(self.key, offset, 1)
        await pipe.execute()
    
    async def exists(self, item: str) -> bool:
        """
        檢查元素是否存在於布隆過濾器中 (異步)
        
        Args:
            item: 要檢查的元素
            
        Returns:
            bool: True 表示可能存在，False 表示一定不存在
        """
        offsets = self._get_offsets(item)
        pipe = self.redis_client.pipeline()
        for offset in offsets:
            pipe.getbit(self.key, offset)
        results = await pipe.execute()
        
        return all(results)
    
    async def add_batch(self, items: List[str]) -> None:
        """
        批量添加元素 (異步)
        
        Args:
            items: 要添加的元素列表
        """
        for item in items:
            await self.add(item)

