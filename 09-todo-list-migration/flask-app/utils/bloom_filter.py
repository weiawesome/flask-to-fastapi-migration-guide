"""
Bloom Filter Implementation
布隆過濾器實作 - 用於快取穿透防護
"""
import mmh3
import math
import redis
import json
from typing import List


class BloomFilter:
    """
    布隆過濾器 - 用於快速判斷 key 是否存在
    解決快取穿透問題：查詢不存在的資料時，先檢查布隆過濾器
    """
    
    def __init__(self, redis_client: redis.Redis, key: str, capacity: int = 10000, error_rate: float = 0.01):
        """
        初始化布隆過濾器
        
        Args:
            redis_client: Redis 客戶端
            key: 布隆過濾器在 Redis 中的 key
            capacity: 預期容量（預期會插入的元素數量）
            error_rate: 誤判率（0-1 之間）
        """
        self.redis_client = redis_client
        self.key = key
        self.capacity = capacity
        self.error_rate = error_rate
        
        # 計算需要的位數和哈希函數數量
        # m = -n * ln(p) / (ln(2)^2)
        # k = m * ln(2) / n
        self.bit_size = int(-capacity * math.log(error_rate) / (math.log(2) ** 2))
        self.hash_count = int(self.bit_size * math.log(2) / capacity)
        
        # 確保至少有 1 個哈希函數
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
            # 使用 mmh3 (MurmurHash3) 進行哈希
            hash_value = mmh3.hash(item, i) % self.bit_size
            offsets.append(hash_value)
        return offsets
    
    def add(self, item: str) -> None:
        """
        添加元素到布隆過濾器
        
        Args:
            item: 要添加的元素
        """
        offsets = self._get_offsets(item)
        pipe = self.redis_client.pipeline()
        for offset in offsets:
            pipe.setbit(self.key, offset, 1)
        pipe.execute()
    
    def exists(self, item: str) -> bool:
        """
        檢查元素是否存在於布隆過濾器中
        
        Args:
            item: 要檢查的元素
            
        Returns:
            bool: True 表示可能存在，False 表示一定不存在
        """
        offsets = self._get_offsets(item)
        pipe = self.redis_client.pipeline()
        for offset in offsets:
            pipe.getbit(self.key, offset)
        results = pipe.execute()
        
        # 所有位都是 1 才表示可能存在
        return all(results)
    
    def add_batch(self, items: List[str]) -> None:
        """
        批量添加元素
        
        Args:
            items: 要添加的元素列表
        """
        for item in items:
            self.add(item)

