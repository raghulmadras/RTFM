# RTFM Bot - Kafka Integration Documentation

## Overview

The RTFM Discord bot uses Apache Kafka as a message broker to decouple message processing from the Discord bot logic. This allows for:

- **Scalability**: Multiple processors can consume messages independently
- **Reliability**: Messages are persisted in Kafka topics
- **Asynchronous processing**: Discord bot doesn't block on AI response generation
- **Separation of concerns**: Clear boundaries between message ingestion, processing, and response delivery

## Architecture

```
Discord → Bot → Kafka → Message Processor → Kafka → Bot → Discord
          |              |                     |            |
          |              |                     |            |
          v              v                     v            v
    discord-messages  ChromaDB           bot-responses  Channel
    bot-queries
```

### Flow

1. **Discord message received** → Bot sends to `discord-messages` topic
2. **Message Processor** consumes from `discord-messages` → stores in ChromaDB
3. **RTFM trigger detected** → Bot sends to `bot-queries` topic
4. **Message Processor** consumes from `bot-queries` → generates AI response → sends to `bot-responses` topic
5. **Bot** consumes from `bot-responses` → sends response to Discord channel

## Kafka Topics

### 1. discord-messages

**Purpose**: All Discord messages for storage in the vector database

**Partitions**: 3
**Retention**: 7 days
**Replication Factor**: 1

**Message Schema**:
```json
{
  "message_id": "1234567890",
  "content": "Hello, this is a test message",
  "username": "user#1234",
  "user_id": "987654321",
  "channel_id": "111222333",
  "timestamp": "2025-11-02T12:34:56.789Z",
  "metadata": {
    "channel_name": "general"
  }
}
```

**Field Descriptions**:
- `message_id` (string): Unique Discord message ID
- `content` (string): The message content/text
- `username` (string): Discord username with discriminator
- `user_id` (string): Unique Discord user ID
- `channel_id` (string): Discord channel ID where message was sent
- `timestamp` (string): ISO 8601 formatted timestamp
- `metadata` (object): Optional additional metadata

**Producers**: `bot.py` (DiscordRTFMBot)
**Consumers**: `message_processor.py` (MessageProcessor)

---

### 2. bot-queries

**Purpose**: User queries that need AI-generated responses

**Partitions**: 3
**Retention**: 1 day
**Replication Factor**: 1

**Message Schema**:
```json
{
  "query_id": "query_abc123",
  "original_message_id": "1234567890",
  "question": "what is the API endpoint?",
  "username": "user#1234",
  "user_id": "987654321",
  "channel_id": "111222333",
  "timestamp": "2025-11-02T12:34:56.789Z",
  "context": {}
}
```

**Field Descriptions**:
- `query_id` (string): Unique identifier for this query (UUID)
- `original_message_id` (string): Discord message ID that triggered this query
- `question` (string): The extracted question (trigger phrase removed)
- `username` (string): Discord username with discriminator
- `user_id` (string): Unique Discord user ID
- `channel_id` (string): Discord channel ID to send response to
- `timestamp` (string): ISO 8601 formatted timestamp
- `context` (object): Optional additional context for the query

**Producers**: `bot.py` (DiscordRTFMBot)
**Consumers**: `message_processor.py` (MessageProcessor)

---

### 3. bot-responses

**Purpose**: AI-generated responses ready to be sent to Discord

**Partitions**: 3
**Retention**: 1 day
**Replication Factor**: 1

**Message Schema**:
```json
{
  "response_id": "response_xyz789",
  "query_id": "query_abc123",
  "original_message_id": "1234567890",
  "response_text": "The API endpoint is /api/v1/data",
  "channel_id": "111222333",
  "timestamp": "2025-11-02T12:34:57.123Z",
  "metadata": {
    "model": "gemini-2.5-flash",
    "confidence": 0.95,
    "sources_count": 3
  }
}
```

**Field Descriptions**:
- `response_id` (string): Unique identifier for this response (UUID)
- `query_id` (string): ID of the query this response answers
- `original_message_id` (string): Original Discord message ID
- `response_text` (string): The AI-generated response text
- `channel_id` (string): Discord channel ID to send response to
- `timestamp` (string): ISO 8601 formatted timestamp
- `metadata` (object): Optional metadata (model used, confidence, etc.)

**Producers**: `message_processor.py` (MessageProcessor)
**Consumers**: `bot.py` (DiscordRTFMBot)

---

## Components

### 1. bot.py - Discord Bot

**Responsibilities**:
- Listen to Discord messages
- Produce to `discord-messages` topic
- Detect RTFM trigger phrases
- Produce to `bot-queries` topic
- Consume from `bot-responses` topic
- Send responses back to Discord channels

**Key Classes**:
- `DiscordRTFMBot`: Main bot class with Kafka integration

### 2. message_processor.py - Message Processor Service

**Responsibilities**:
- Consume from `discord-messages` topic → store in ChromaDB
- Consume from `bot-queries` topic → generate AI responses
- Produce to `bot-responses` topic

**Key Classes**:
- `MessageProcessor`: Main processor with AI generation

### 3. kafka_producer.py - Kafka Producer

**Responsibilities**:
- Send messages to Kafka topics
- Handle serialization
- Manage producer connections

**Key Classes**:
- `RTFMKafkaProducer`: Producer with methods for each topic

### 4. kafka_consumer.py - Kafka Consumers

**Responsibilities**:
- Consume messages from Kafka topics
- Handle deserialization
- Manage consumer groups and offsets

**Key Classes**:
- `RTFMKafkaConsumer`: Base consumer class
- `DiscordMessageConsumer`: Consumer for discord-messages
- `BotQueryConsumer`: Consumer for bot-queries
- `BotResponseConsumer`: Consumer for bot-responses
- `MultiConsumerManager`: Manages multiple consumers

### 5. schemas.py - Message Schemas

**Responsibilities**:
- Define TypedDict schemas for messages
- Provide serialization/deserialization helpers
- Document message formats

**Key Classes**:
- `SchemaValidator`: Validation and serialization utilities

---

## Setup and Usage

### 1. Initialize Kafka Topics

Before running the bot, create the required Kafka topics:

```bash
python init_kafka_topics.py --bootstrap-servers localhost:29092 --action create
```

List existing topics:
```bash
python init_kafka_topics.py --bootstrap-servers localhost:29092 --action list
```

Delete topics (for cleanup):
```bash
python init_kafka_topics.py --bootstrap-servers localhost:29092 --action delete
```

### 2. Run Message Processor

Start the message processor service (should run continuously):

```bash
python message_processor.py
```

### 3. Run Discord Bot

Start the Discord bot:

```bash
python bot.py
```

### 4. Test Kafka Integration

Run the test script to verify producer/consumer functionality:

```bash
# Test all topics
python test_kafka.py --bootstrap-servers localhost:29092 --test all

# Test specific topic
python test_kafka.py --bootstrap-servers localhost:29092 --test discord
python test_kafka.py --bootstrap-servers localhost:29092 --test queries
python test_kafka.py --bootstrap-servers localhost:29092 --test responses
```

---

## Docker Compose Integration

The bot is designed to run with Docker Compose. The Kafka configuration is in `docker-compose.yml`:

```yaml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports:
      - "9092:9092"
      - "29092:29092"
    depends_on:
      - zookeeper
    environment:
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:29092
```

**Note**:
- Use `kafka:9092` when connecting from within Docker network
- Use `localhost:29092` when connecting from host machine

---

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092  # Use kafka:9092 in Docker, localhost:29092 on host

# Existing variables
DISCORD_TOKEN=your_token
GEMINI_API_KEY=your_key
```

### Producer Configuration

Producers are configured with:
- `acks='all'`: Wait for all replicas to acknowledge
- `retries=3`: Retry failed sends up to 3 times
- `max_in_flight_requests_per_connection=1`: Ensure message ordering

### Consumer Configuration

Consumers are configured with:
- `auto_offset_reset='latest'`: Start from latest messages (change to 'earliest' for replay)
- `enable_auto_commit=True`: Automatically commit offsets
- `auto_commit_interval_ms=1000`: Commit every second

---

## Monitoring

### Kafka Topic Metrics

Check topic status:
```bash
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --describe --topic discord-messages
```

Check consumer group status:
```bash
docker exec -it kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group discord-message-processor
```

### Application Logs

Both `bot.py` and `message_processor.py` use Python's logging module with INFO level by default.

---

## Troubleshooting

### Messages not being consumed

1. Check if topics exist:
   ```bash
   python init_kafka_topics.py --action list
   ```

2. Check consumer group lag:
   ```bash
   docker exec -it kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group bot-query-processor
   ```

3. Check Kafka logs:
   ```bash
   docker logs kafka
   ```

### Connection refused errors

- Ensure Kafka is running: `docker ps | grep kafka`
- Verify bootstrap servers address (kafka:9092 vs localhost:29092)
- Wait for Kafka to fully start (can take 30-60 seconds)

### Messages being duplicated

- Check if multiple consumers are running in the same consumer group
- Verify auto-commit is working properly

---

## Performance Considerations

### Partitioning

Topics are configured with 3 partitions to allow parallel processing. Key-based partitioning ensures messages from the same user/channel go to the same partition.

### Retention

- `discord-messages`: 7 days (allows reprocessing historical messages)
- `bot-queries`: 1 day (queries are processed quickly)
- `bot-responses`: 1 day (responses are delivered quickly)

### Scaling

To scale processing:
1. Increase topic partitions
2. Run multiple `message_processor.py` instances
3. Each processor will join the consumer group and share the load

---

## Future Enhancements

- [ ] Add dead letter queue for failed messages
- [ ] Implement circuit breaker for AI API calls
- [ ] Add metrics/monitoring with Prometheus
- [ ] Implement message compression
- [ ] Add schema registry for message validation
- [ ] Implement exactly-once semantics
