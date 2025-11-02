"""
============================================================================
RTFM Discord Bot - Kafka Producer
============================================================================

This module handles producing messages to Kafka topics.
"""

from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RTFMKafkaProducer:
    """
    Kafka producer for RTFM bot messages

    Handles sending messages to the three main topics:
    - discord-messages
    - bot-queries
    - bot-responses
    """

    TOPIC_DISCORD_MESSAGES = "discord-messages"
    TOPIC_BOT_QUERIES = "bot-queries"
    TOPIC_BOT_RESPONSES = "bot-responses"

    def __init__(self, bootstrap_servers: str = "kafka:9092"):
        """
        Initialize Kafka producer

        Args:
            bootstrap_servers: Kafka broker address
        """
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self._connect()

    def _connect(self):
        """Establish connection to Kafka broker"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info(f"Connected to Kafka broker at {self.bootstrap_servers}")
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    def send_discord_message(
        self,
        message_data: dict,
        key: Optional[str] = None
    ) -> bool:
        """
        Send a Discord message to the discord-messages topic

        Args:
            message_data: Dictionary containing message data
            key: Optional message key for partitioning

        Returns:
            True if sent successfully, False otherwise
        """
        return self._send_message(
            self.TOPIC_DISCORD_MESSAGES,
            message_data,
            key or message_data.get('message_id')
        )

    def send_bot_query(
        self,
        query_data: dict,
        key: Optional[str] = None
    ) -> bool:
        """
        Send a bot query to the bot-queries topic

        Args:
            query_data: Dictionary containing query data
            key: Optional query key for partitioning

        Returns:
            True if sent successfully, False otherwise
        """
        return self._send_message(
            self.TOPIC_BOT_QUERIES,
            query_data,
            key or query_data.get('query_id')
        )

    def send_bot_response(
        self,
        response_data: dict,
        key: Optional[str] = None
    ) -> bool:
        """
        Send a bot response to the bot-responses topic

        Args:
            response_data: Dictionary containing response data
            key: Optional response key for partitioning

        Returns:
            True if sent successfully, False otherwise
        """
        return self._send_message(
            self.TOPIC_BOT_RESPONSES,
            response_data,
            key or response_data.get('response_id')
        )

    def _send_message(
        self,
        topic: str,
        message: dict,
        key: Optional[str] = None
    ) -> bool:
        """
        Internal method to send a message to a Kafka topic

        Args:
            topic: Kafka topic name
            message: Message data as dictionary
            key: Optional message key

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            future = self.producer.send(topic, value=message, key=key)
            # Block for synchronous send (optional, can be made async)
            record_metadata = future.get(timeout=10)
            logger.info(
                f"Message sent to {topic} "
                f"[partition: {record_metadata.partition}, "
                f"offset: {record_metadata.offset}]"
            )
            return True
        except KafkaError as e:
            logger.error(f"Failed to send message to {topic}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message to {topic}: {e}")
            return False

    def flush(self):
        """Flush any pending messages"""
        if self.producer:
            self.producer.flush()

    def close(self):
        """Close the producer connection"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka producer closed")


# Singleton instance for easy import
_producer_instance: Optional[RTFMKafkaProducer] = None


def get_producer(bootstrap_servers: str = "kafka:9092") -> RTFMKafkaProducer:
    """
    Get or create singleton producer instance

    Args:
        bootstrap_servers: Kafka broker address

    Returns:
        RTFMKafkaProducer instance
    """
    global _producer_instance
    if _producer_instance is None:
        _producer_instance = RTFMKafkaProducer(bootstrap_servers)
    return _producer_instance


if __name__ == "__main__":
    # Test the producer
    logging.basicConfig(level=logging.INFO)

    producer = RTFMKafkaProducer(bootstrap_servers="localhost:29092")

    # Test discord-messages topic
    test_message = {
        "message_id": "test123",
        "content": "Test message",
        "username": "testuser",
        "user_id": "123456",
        "channel_id": "789012",
        "timestamp": "2025-11-02T12:00:00Z",
        "metadata": {}
    }

    producer.send_discord_message(test_message)
    producer.close()
    print("Test message sent successfully")
