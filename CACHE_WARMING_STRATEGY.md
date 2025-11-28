# Cache Warming Strategy

## Overview
Pre-populate Redis cache with frequently accessed queries to improve first-request performance.

## Popular Query Patterns
Based on server analysis, these queries are warmed on startup:
- "meeting time"
- "deadline"
- "setup instructions"
- [Add your server's common queries]

## Warming Schedule
- **On startup**: All popular queries are cached immediately
- **Periodic refresh**: Every 30 minutes, popular queries are re-cached
- **TTL**: Cached queries expire after 1 hour

## Cache Hit Rate Monitoring
- Target hit rate: >70%
- Metrics logged every hour
- Stored in Redis keys: `stats:cache_hits`, `stats:cache_misses`

## Performance Impact
- Cold start: ~5-10s to warm cache with 10 queries
- Warm cache: <100ms for cached queries
- Memory usage: ~1MB per 100 cached queries
