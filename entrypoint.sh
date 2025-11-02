#!/bin/bash
# ============================================================================
# RTFM Discord Bot - Docker Entrypoint
# ============================================================================

set -e

echo "Starting RTFM Bot..."

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
until python -c "from kafka import KafkaAdminClient; KafkaAdminClient(bootstrap_servers='kafka:9092').list_topics()" 2>/dev/null; do
    echo "Kafka is unavailable - sleeping"
    sleep 5
done

echo "Kafka is ready!"

# Initialize Kafka topics if this is the message processor
if [ "$1" = "message_processor.py" ]; then
    echo "Initializing Kafka topics..."
    python init_kafka_topics.py --bootstrap-servers kafka:9092 --action create || true
    echo "Kafka topics initialized"
fi

# Execute the command
echo "Starting application: $@"
exec python "$@"
