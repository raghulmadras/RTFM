# RTFM Bot - System Architecture

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         RTFM Discord Bot System                          │
└──────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   Discord   │
                              │   Server    │
                              └──────┬──────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
            ┌───────────┐    ┌───────────┐   ┌───────────┐
            │ Message 1 │    │ Message 2 │   │ Message 3 │
            │  (RTFM?)  │    │(normal msg)│   │  (RTFM?)  │
            └─────┬─────┘    └─────┬─────┘   └─────┬─────┘
                  │                │                │
                  └────────────────┼────────────────┘
                                   │
                                   ▼
                         ┌──────────────────┐
                         │   Discord Bot    │
                         │    (bot.py)      │
                         │                  │
                         │ • Listen to msgs │
                         │ • Detect RTFM    │
                         │ • Send to Kafka  │
                         │ • Send responses │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
         ┌──────────▼──────┐     │     ┌───────▼────────┐
         │ discord-messages│     │     │  bot-queries   │
         │  Kafka Topic    │     │     │  Kafka Topic   │
         └────────┬────────┘     │     └───────┬────────┘
                  │              │             │
                  │              │             │
                  │    ┌─────────▼──────┐      │
                  │    │   Kafka Broker │      │
                  │    │                │      │
                  │    │ • Persistence  │      │
                  │    │ • Partitioning │      │
                  │    │ • Replication  │      │
                  │    └────────────────┘      │
                  │                            │
                  └──────────────┬─────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  Message Processor     │
                    │ (message_processor.py) │
                    │                        │
                    │ • Store messages       │
                    │ • Process queries      │
                    │ • Generate responses   │
                    └───┬────────────────┬───┘
                        │                │
          ┌─────────────┘                └─────────────┐
          │                                            │
          ▼                                            ▼
    ┌──────────┐                               ┌──────────────┐
    │ ChromaDB │                               │ Gemini API   │
    │          │                               │              │
    │ • Vector │                               │ • Query LLM  │
    │   store  │                               │ • Generate   │
    │ • Search │                               │   responses  │
    └──────────┘                               └──────┬───────┘
                                                      │
                                                      │
                                              ┌───────▼────────┐
                                              │ bot-responses  │
                                              │  Kafka Topic   │
                                              └───────┬────────┘
                                                      │
                                                      │
                                                      ▼
                                              ┌───────────────┐
                                              │ Discord Bot   │
                                              │  (consumer)   │
                                              └───────┬───────┘
                                                      │
                                                      ▼
                                              ┌───────────────┐
                                              │    Discord    │
                                              │    Channel    │
                                              └───────────────┘
```

## Component Details

### 1. Discord Bot (`bot.py`)

**Purpose**: Interface between Discord and Kafka

**Responsibilities**:
- Listen to all Discord messages
- Produce messages to `discord-messages` topic
- Detect RTFM trigger phrases
- Produce queries to `bot-queries` topic
- Consume responses from `bot-responses` topic
- Send responses back to Discord

**Technology**: discord.py, kafka-python

---

### 2. Message Processor (`message_processor.py`)

**Purpose**: Process messages and generate AI responses

**Responsibilities**:
- Consume from `discord-messages` → store in ChromaDB
- Consume from `bot-queries` → generate AI responses
- Produce responses to `bot-responses` topic

**Technology**: kafka-python, ChromaDB, Google Gemini API

---

### 3. Kafka Broker

**Purpose**: Message broker for async communication

**Topics**:
- `discord-messages`: Raw Discord messages (7 day retention)
- `bot-queries`: User queries (1 day retention)
- `bot-responses`: AI responses (1 day retention)

**Configuration**:
- 3 partitions per topic
- Replication factor: 1
- Persistence enabled

---

### 4. ChromaDB

**Purpose**: Vector database for semantic search

**Functionality**:
- Store message embeddings
- Semantic search for relevant context
- Provide context for AI responses

**Model**: sentence-transformers/all-MiniLM-L6-v2

---

### 5. Gemini API

**Purpose**: Generate AI responses

**Functionality**:
- Receive context from ChromaDB
- Generate natural language responses
- Answer user queries

**Model**: gemini-2.5-flash

---

## Message Flow Diagrams

### Normal Message Flow

```
1. User sends message: "Hello everyone!"

   Discord → Bot → Kafka (discord-messages) → Processor → ChromaDB
                                                            (stored)
```

### RTFM Query Flow

```
2. User asks: "RTFM what is the API endpoint?"

   Discord → Bot → Kafka (discord-messages) → Processor → ChromaDB
                                                            (stored)
              │
              └─→ Kafka (bot-queries) → Processor → ChromaDB (search)
                                            │            │
                                            │            ▼
                                            │       [relevant msgs]
                                            │            │
                                            └─→ Gemini ◄─┘
                                                   │
                                                   ▼
                                            [AI response]
                                                   │
                                                   ▼
                                        Kafka (bot-responses)
                                                   │
                                                   ▼
                                           Bot (consumer)
                                                   │
                                                   ▼
                                               Discord
                                                   │
                                                   ▼
                                          "The API endpoint..."
```

## Data Flow Details

### 1. Message Ingestion

```
Discord Message
    │
    ├─ message_id: "123456"
    ├─ content: "Hello world"
    ├─ username: "user#1234"
    ├─ channel_id: "789"
    └─ timestamp: "2025-11-02T12:00:00Z"
    │
    ▼
Kafka (discord-messages)
    │
    ▼
Message Processor
    │
    ├─ Generate embedding
    └─ Store in ChromaDB
```

### 2. Query Processing

```
RTFM Query
    │
    ├─ query_id: "uuid-123"
    ├─ question: "what is the API?"
    ├─ channel_id: "789"
    └─ timestamp: "2025-11-02T12:05:00Z"
    │
    ▼
Kafka (bot-queries)
    │
    ▼
Message Processor
    │
    ├─ Query ChromaDB
    │   └─ Get top 5 relevant messages
    │
    ├─ Build context prompt
    │
    ├─ Call Gemini API
    │   └─ Generate response
    │
    └─ Produce to bot-responses
        │
        ├─ response_id: "uuid-456"
        ├─ query_id: "uuid-123"
        ├─ response_text: "The API endpoint is..."
        └─ channel_id: "789"
```

### 3. Response Delivery

```
Kafka (bot-responses)
    │
    ▼
Bot (consumer)
    │
    ├─ Extract channel_id
    ├─ Extract response_text
    │
    └─ Send to Discord channel
        │
        ▼
    Discord Channel
```

## Scalability

### Horizontal Scaling

```
┌─────────────────────────────────────────────┐
│              Load Balancing                 │
└─────────────────────────────────────────────┘

        ┌────────────┐
        │   Kafka    │
        │  (3 parts) │
        └──────┬─────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│Proc #1 │ │Proc #2 │ │Proc #3 │
│Part 0  │ │Part 1  │ │Part 2  │
└────────┘ └────────┘ └────────┘
```

**Scaling Strategy**:
- Add more partitions to topics
- Run multiple message processor instances
- Each processor joins consumer group
- Kafka distributes partitions automatically

### Vertical Scaling

- Increase Kafka broker resources
- Increase ChromaDB memory
- Use faster embeddings model

## Fault Tolerance

### Message Persistence

```
Message → Kafka → Persisted to disk
                   │
                   ├─ Retention: 7 days (discord-messages)
                   ├─ Retention: 1 day (bot-queries)
                   └─ Retention: 1 day (bot-responses)
```

### Consumer Groups

```
Consumer Group: "discord-message-processor"
    │
    ├─ Consumer 1 (running) ✓
    ├─ Consumer 2 (crashed) ✗
    └─ Consumer 3 (running) ✓

Kafka automatically rebalances:
    │
    └─ Partitions redistributed to healthy consumers
```

### Retry Logic

```
Producer → Kafka
    │
    ├─ Attempt 1: Failed ✗
    ├─ Attempt 2: Failed ✗
    └─ Attempt 3: Success ✓

Configuration:
    • retries=3
    • acks='all' (wait for replication)
```

## Monitoring

### Metrics to Track

1. **Kafka Metrics**
   - Consumer lag
   - Message throughput
   - Partition distribution

2. **Application Metrics**
   - Messages processed/second
   - AI response latency
   - Error rates

3. **Infrastructure Metrics**
   - CPU/Memory usage
   - Disk I/O
   - Network bandwidth

### Monitoring Tools

- Prometheus (metrics collection)
- Grafana (visualization)
- Kafka built-in tools

## Security Considerations

### API Keys

```
.env file (not in git):
    DISCORD_TOKEN=secret_token
    GEMINI_API_KEY=secret_key
    KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

### Network Security

```
Docker Network: rtfm-network
    │
    ├─ Bot (internal)
    ├─ Processor (internal)
    ├─ Kafka (internal + external:29092)
    └─ ChromaDB (internal)

Only bot has internet access for Discord/Gemini
```

## Deployment

### Docker Compose Services

```yaml
services:
  - zookeeper      # Kafka coordination
  - kafka          # Message broker
  - bot            # Discord interface
  - message-processor  # AI processing
  - chroma         # Vector database
  - prometheus     # Metrics
  - grafana        # Monitoring
  - postgres       # Future use
  - redis          # Future use
```

### Startup Order

```
1. Zookeeper
2. Kafka
3. ChromaDB
4. Message Processor (initializes topics)
5. Bot
```

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11 |
| Discord | discord.py | 2.3.2 |
| Kafka Client | kafka-python | 2.0.2 |
| Vector DB | ChromaDB | 0.4.18 |
| Embeddings | sentence-transformers | 2.2.2 |
| AI API | Google Gemini | 2.5-flash |
| Message Broker | Apache Kafka | 7.5.0 |
| Coordination | Zookeeper | 7.5.0 |
| Containerization | Docker | - |
| Orchestration | Docker Compose | - |

## Summary

The RTFM bot uses a modern microservices architecture with:

✅ **Decoupled components** - Each service has a single responsibility
✅ **Asynchronous processing** - Kafka enables non-blocking operations
✅ **Scalability** - Can scale horizontally by adding processors
✅ **Reliability** - Message persistence and retry logic
✅ **Maintainability** - Clear separation of concerns

This architecture supports future enhancements while maintaining stability and performance.
