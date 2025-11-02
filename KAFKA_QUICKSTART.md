# Kafka Integration - Quick Start Guide

## Overview

The RTFM bot now uses Kafka for message processing, creating a decoupled architecture:

```
Discord → Bot → Kafka → Processor → Kafka → Bot → Discord
```

## Quick Start

### 1. Start the System

```bash
# Build and start all services
make init

# Or manually:
docker-compose up -d
```

This will start:
- Zookeeper
- Kafka
- Bot (Discord integration)
- Message Processor (AI processing)
- ChromaDB (Vector database)
- PostgreSQL, Redis, Prometheus, Grafana

### 2. Verify Kafka Topics

Check that topics were created:

```bash
make list-topics
```

You should see:
- `discord-messages`
- `bot-queries`
- `bot-responses`

### 3. View Logs

```bash
# Bot logs
make logs

# Message processor logs
make logs-processor

# All services
make logs-all
```

### 4. Test Kafka Integration

```bash
make test-kafka
```

## Architecture

### Services

1. **rtfm-bot** (`bot.py`)
   - Listens to Discord messages
   - Sends messages to `discord-messages` topic
   - Sends queries to `bot-queries` topic
   - Consumes from `bot-responses` topic
   - Sends responses back to Discord

2. **rtfm-message-processor** (`message_processor.py`)
   - Consumes from `discord-messages` → stores in ChromaDB
   - Consumes from `bot-queries` → generates AI responses
   - Sends responses to `bot-responses` topic

### Message Flow

1. **User sends Discord message**
   ```
   Discord → bot.py → discord-messages (Kafka)
   ```

2. **Message stored in vector DB**
   ```
   discord-messages (Kafka) → message_processor.py → ChromaDB
   ```

3. **User asks question with RTFM trigger**
   ```
   Discord → bot.py → bot-queries (Kafka)
   ```

4. **AI generates response**
   ```
   bot-queries (Kafka) → message_processor.py → Gemini API → bot-responses (Kafka)
   ```

5. **Response sent to Discord**
   ```
   bot-responses (Kafka) → bot.py → Discord
   ```

## Kafka Topics

### discord-messages
- **Purpose**: All Discord messages for storage
- **Partitions**: 3
- **Retention**: 7 days

### bot-queries
- **Purpose**: User queries needing AI responses
- **Partitions**: 3
- **Retention**: 1 day

### bot-responses
- **Purpose**: AI-generated responses
- **Partitions**: 3
- **Retention**: 1 day

## Files Created

### Core Integration
- `kafka_producer.py` - Kafka producer
- `kafka_consumer.py` - Kafka consumers
- `message_processor.py` - Message processing service
- `schemas.py` - Message schemas
- `init_kafka_topics.py` - Topic initialization
- `test_kafka.py` - Integration tests

### Updated Files
- `bot.py` - Now uses Kafka
- `docker-compose.yml` - Added message-processor service
- `Dockerfile` - Added Kafka-related files
- `requirements.txt` - Added kafka-python
- `Makefile` - Added Kafka commands

### Documentation
- `KAFKA_INTEGRATION.md` - Full documentation
- `KAFKA_QUICKSTART.md` - This file

## Useful Commands

```bash
# View bot logs
make logs

# View processor logs
make logs-processor

# View all logs
make logs-all

# Check service status
make status

# Test Kafka
make test-kafka

# List topics
make list-topics

# Initialize topics manually (if needed)
make init-topics

# Restart everything
make restart

# Rebuild everything
make rebuild
```

## Troubleshooting

### Bot not connecting to Kafka

Check if Kafka is running:
```bash
docker-compose ps kafka
```

Check Kafka logs:
```bash
docker-compose logs kafka
```

### Topics not created

Manually create topics:
```bash
make init-topics
```

### Messages not being processed

1. Check if message processor is running:
   ```bash
   docker-compose ps message-processor
   ```

2. Check processor logs:
   ```bash
   make logs-processor
   ```

3. Check Kafka consumer groups:
   ```bash
   docker-compose exec kafka kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --describe \
     --group discord-message-processor
   ```

### Testing without Discord

You can test the Kafka integration directly:

```bash
# From host machine
python test_kafka.py --bootstrap-servers localhost:29092 --test all

# Or inside Docker
make test-kafka
```

## Environment Variables

Add to your `.env` file:

```bash
# Required
DISCORD_TOKEN=your_discord_token_here
GEMINI_API_KEY=your_gemini_key_here

# Optional (defaults shown)
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

## Performance Tips

### Scaling Message Processing

To process messages faster, you can run multiple message processors:

```bash
docker-compose up -d --scale message-processor=3
```

Each processor will join the consumer group and share the load.

### Monitoring

Check consumer lag:
```bash
docker-compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --all-groups
```

## Next Steps

1. ✅ Kafka integration complete
2. ✅ Topics defined and created
3. ✅ Producer/consumer implemented
4. ✅ Bot integrated with Kafka
5. ✅ Message processor service created
6. ✅ Tests written
7. ✅ Documentation complete

### Future Enhancements

- [ ] Add dead letter queue for failed messages
- [ ] Implement circuit breaker for AI API
- [ ] Add Prometheus metrics for Kafka
- [ ] Implement exactly-once semantics
- [ ] Add schema registry
- [ ] Implement message compression

## Support

For detailed documentation, see `KAFKA_INTEGRATION.md`.

For issues, check:
1. Service logs: `make logs-all`
2. Service status: `make status`
3. Kafka topics: `make list-topics`
