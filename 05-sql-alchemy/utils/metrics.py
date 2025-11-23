"""
Metrics Collector
效能指標收集器 - 記錄 API 效能資料
"""
from collections import defaultdict
from typing import Dict, List
import statistics


class MetricsCollector:
    """
    效能指標收集器
    記錄每個端點的請求次數、回應時間等
    """
    
    def __init__(self):
        # 儲存每個端點的回應時間
        self.response_times: Dict[str, List[float]] = defaultdict(list)
        
        # 儲存每個端點的請求次數
        self.request_counts: Dict[str, int] = defaultdict(int)
        
        # 儲存每個狀態碼的次數
        self.status_codes: Dict[int, int] = defaultdict(int)
    
    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float
    ):
        """
        記錄單個請求的指標
        
        Args:
            method: HTTP 方法
            path: 路徑
            status_code: 狀態碼
            duration: 回應時間（秒）
        """
        endpoint = f"{method} {path}"
        
        # 記錄回應時間
        self.response_times[endpoint].append(duration)
        
        # 記錄請求次數
        self.request_counts[endpoint] += 1
        
        # 記錄狀態碼
        self.status_codes[status_code] += 1
    
    def get_stats(self, endpoint: str | None = None) -> Dict:
        """
        獲取統計資料
        
        Args:
            endpoint: 特定端點（如 "GET /users"），None 表示所有端點
        
        Returns:
            Dict: 統計資料
        """
        if endpoint:
            # 特定端點的統計
            times = self.response_times.get(endpoint, [])
            if not times:
                return {"error": "No data for this endpoint"}
            
            return {
                "endpoint": endpoint,
                "total_requests": self.request_counts[endpoint],
                "avg_response_time": statistics.mean(times),
                "min_response_time": min(times),
                "max_response_time": max(times),
                "median_response_time": statistics.median(times),
            }
        else:
            # 所有端點的統計
            return {
                "total_endpoints": len(self.request_counts),
                "total_requests": sum(self.request_counts.values()),
                "endpoints": [
                    {
                        "endpoint": ep,
                        "requests": count,
                        "avg_time": statistics.mean(self.response_times[ep])
                    }
                    for ep, count in self.request_counts.items()
                ],
                "status_codes": dict(self.status_codes)
            }
    
    def reset(self):
        """重置所有統計資料"""
        self.response_times.clear()
        self.request_counts.clear()
        self.status_codes.clear()
    
    def is_enabled(self) -> bool:
        """檢查指標收集器是否啟用"""
        return True
    
    def get_summary(self) -> Dict:
        """獲取摘要資訊"""
        total_requests = sum(self.request_counts.values())
        if total_requests == 0:
            return {
                "total_requests": 0,
                "total_endpoints": 0,
                "message": "No requests recorded yet"
            }
        
        return {
            "total_requests": total_requests,
            "total_endpoints": len(self.request_counts),
            "status_codes": dict(self.status_codes)
        }


# 全域單例
metrics_collector = MetricsCollector()

