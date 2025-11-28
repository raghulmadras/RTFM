# cache_warmer.py
import redis
import logging
import hashlib
import json
import asyncio
from typing import List
from datetime import datetime
from cache_warming_config import POPULAR_QUERIES

logger = logging.getLogger(__name__)

class CacheWarmer:
    def __init__(self, redis_client: redis.Redis, vector_search_func):
        self.redis = redis_client
        self.vector_search = vector_search_func
    
    # TASK 2: Cache warming on startup
    def warm_cache_on_startup(self, server_id: str):
        """
        Pre-populate cache with popular queries when service starts
        """
        logger.info(f"Starting cache warming for server {server_id}")
        
        warmed_count = 0
        for query in POPULAR_QUERIES:
            try:
                # Generate cache key
                query_hash = hashlib.md5(query.lower().encode()).hexdigest()
                cache_key = f"query:{server_id}:{query_hash}"
                
                # Check if already cached
                if self.redis.exists(cache_key):
                    logger.debug(f"Query already cached: {query}")
                    continue
                
                # Execute search and cache result
                results = self.vector_search(query, server_id)
                
                # Store in Redis with TTL (1 hour)
                self.redis.setex(
                    cache_key,
                    3600,  # 1 hour TTL
                    json.dumps(results)
                )
                
                warmed_count += 1
                logger.info(f"Warmed cache for query: '{query}'")
                
            except Exception as e:
                logger.error(f"Failed to warm cache for '{query}': {e}")
        
        logger.info(f"Cache warming complete: {warmed_count}/{len(POPULAR_QUERIES)} queries cached")
    
    async def periodic_cache_refresh(self, server_id: str, interval_minutes: int = 30):
        """
        Periodically refresh cache for popular queries
        Runs every 'interval_minutes' minutes
        """
        logger.info(f"Starting periodic cache refresh (every {interval_minutes} min)")
        
        while True:
            try:
                await asyncio.sleep(interval_minutes * 60)
                
                logger.info(f"Running periodic cache refresh at {datetime.now()}")
                self.warm_cache_on_startup(server_id)
                
            except Exception as e:
                logger.error(f"Error in periodic refresh: {e}")
                await asyncio.sleep(60)  # Wait 1 min before retry
