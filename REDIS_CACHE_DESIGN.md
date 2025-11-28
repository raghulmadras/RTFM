# Redis Cache Design for RTFM Bot

## Cache Key Naming Convention

All cache keys follow this format: `{prefix}:{server_id}:{identifier}`

### Key Patterns

1. **Search Query Results**
   - Format: `query:{server_id}:{hash(question)}`
   - Example: `query:123456789:a3f5e8d9c2b1`
   - Purpose: Cache semantic search results to avoid re-running expensive vector searches
   - Hash function: MD5 of the normalized query string

2. **Message Embeddings**
   - Format: `embed:{server_id}:{message_id}`
   - Example: `embed:123456789:987654321`
   - Purpose: Cache vector embeddings to avoid repeated API calls to HuggingFace

3. **User Search History**
   - Format: `history:{server_id}:{user_id}`
   - Example: `history:123456789:111222333`
   - Purpose: Track recent user searches for analytics

4. **Rate Limiting**
   - Format: `ratelimit:{user_id}:{command}`
   - Example: `ratelimit:111222333:search`
   - Purpose: Prevent abuse by limiting requests per user

5. **Recent Messages Cache**
   - Format: `messages:{server_id}:{channel_id}`
   - Example: `messages:123456789:444555666`
   - Purpose: Cache recent channel messages to reduce Discord API calls

## TTL (Time To Live) Strategy

| Cache Key Pattern | TTL (seconds) | TTL (human) | Reasoning |
|------------------|---------------|-------------|-----------|
| `query:{server_id}:{hash}` | 3600 | 1 hour | Search results become stale as new messages arrive; 1 hour balances freshness with performance |
| `embed:{server_id}:{message_id}` | 86400 | 24 hours | Message embeddings don't change unless message is edited/deleted |
| `history:{server_id}:{user_id}` | 1800 | 30 minutes | Recent search history for quick access; doesn't need long persistence |
| `ratelimit:{user_id}:{command}` | 60 | 1 minute | Per-minute rate limiting window |
| `messages:{server_id}:{channel_id}` | 300 | 5 minutes | Recent messages cache; frequently updated as users chat |

## Cache Invalidation Approach

### Invalidation Triggers

1. **New Message Event**
   - When: A new message is posted in any channel
   - Invalidate: 
     - `query:{server_id}:*` (all search queries for that server)
     - `messages:{server_id}:{channel_id}` (messages in that channel)
   - Reason: New messages could change search results

2. **Message Deleted Event**
   - When: A message is deleted
   - In
