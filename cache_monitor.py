import redis
import logging

logger = logging.getLogger(__name__)

class CacheMonitor:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.hits = 0
        self.misses = 0
    
    def record_hit(self):
        """Record a cache hit"""
        self.hits += 1
        self.redis.incr("stats:cache_hits")
    
    def record_miss(self):
        """Record a cache miss"""
        self.misses += 1
        self.redis.incr("stats:cache_misses")
    
    def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100
    
    def log_stats(self):
        """Log cache statistics"""
        hit_rate = self.get_hit_rate()
        logger.info(f"Cache Stats - Hits: {self.hits}, Misses: {self.misses}, Hit Rate: {hit_rate:.2f}%")
        
        # Get Redis info
        info = self.redis.info('stats')
        logger.info(f"Redis Stats - Keys: {self.redis.dbsize()}, Memory: {info.get('used_memory_human')}")
