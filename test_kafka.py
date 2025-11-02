"""
============================================================================
RTFM Discord Bot - Kafka Producer/Consumer Test
============================================================================

This script tests the Kafka producer and consumer functionality.
"""

import time
import logging
import uuid
from datetime import datetime
from kafka_producer import RTFMKafkaProducer
from kafka_consumer import (
    DiscordMessageConsumer,
    BotQueryConsumer,
    BotResponseConsumer
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KafkaTest:
    """Test Kafka producer and consumer functionality"""

    def __init__(self, bootstrap_servers: str = "localhost:29092"):
        self.bootstrap_servers = bootstrap_servers
        self.messages_received = []

    def test_discord_messages(self):
        """Test discord-messages topic"""
        logger.info("=== Testing discord-messages topic ===")

        # Create producer
        producer = RTFMKafkaProducer(self.bootstrap_servers)

        # Create consumer
        consumer = DiscordMessageConsumer(self.bootstrap_servers, group_id="test-group-1")

        # Define message handler
        def message_handler(msg: dict):
            logger.info(f"✓ Received Discord message: {msg}")
            self.messages_received.append(msg)

        # Start consumer in background
        thread = consumer.consume_async(message_handler)

        # Give consumer time to connect
        time.sleep(3)

        # Send test messages
        test_messages = [
            {
                "message_id": str(uuid.uuid4()),
                "content": "Hello, this is a test message",
                "username": "TestUser#1234",
                "user_id": "123456789",
                "channel_id": "987654321",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {"test": True}
            },
            {
                "message_id": str(uuid.uuid4()),
                "content": "RTFM what is the API endpoint?",
                "username": "AnotherUser#5678",
                "user_id": "111222333",
                "channel_id": "444555666",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {"test": True}
            }
        ]

        for msg in test_messages:
            success = producer.send_discord_message(msg)
            if success:
                logger.info(f"✓ Sent Discord message: {msg['content'][:50]}")
            else:
                logger.error(f"✗ Failed to send Discord message")

        # Wait for messages to be consumed
        logger.info("Waiting for messages to be consumed...")
        time.sleep(5)

        # Cleanup
        consumer.stop()
        producer.close()

        # Verify
        if len(self.messages_received) >= len(test_messages):
            logger.info(f"✓ SUCCESS: Received {len(self.messages_received)} messages")
        else:
            logger.error(
                f"✗ FAILED: Expected {len(test_messages)} messages, "
                f"received {len(self.messages_received)}"
            )

        self.messages_received.clear()

    def test_bot_queries(self):
        """Test bot-queries topic"""
        logger.info("\n=== Testing bot-queries topic ===")

        # Create producer
        producer = RTFMKafkaProducer(self.bootstrap_servers)

        # Create consumer
        consumer = BotQueryConsumer(self.bootstrap_servers, group_id="test-group-2")

        # Define message handler
        def query_handler(query: dict):
            logger.info(f"✓ Received bot query: {query['question']}")
            self.messages_received.append(query)

        # Start consumer in background
        thread = consumer.consume_async(query_handler)

        # Give consumer time to connect
        time.sleep(3)

        # Send test queries
        test_queries = [
            {
                "query_id": str(uuid.uuid4()),
                "original_message_id": str(uuid.uuid4()),
                "question": "What is the API endpoint?",
                "username": "TestUser#1234",
                "user_id": "123456789",
                "channel_id": "987654321",
                "timestamp": datetime.utcnow().isoformat(),
                "context": {}
            },
            {
                "query_id": str(uuid.uuid4()),
                "original_message_id": str(uuid.uuid4()),
                "question": "How do I configure the database?",
                "username": "AnotherUser#5678",
                "user_id": "111222333",
                "channel_id": "444555666",
                "timestamp": datetime.utcnow().isoformat(),
                "context": {}
            }
        ]

        for query in test_queries:
            success = producer.send_bot_query(query)
            if success:
                logger.info(f"✓ Sent bot query: {query['question']}")
            else:
                logger.error(f"✗ Failed to send bot query")

        # Wait for messages to be consumed
        logger.info("Waiting for queries to be consumed...")
        time.sleep(5)

        # Cleanup
        consumer.stop()
        producer.close()

        # Verify
        if len(self.messages_received) >= len(test_queries):
            logger.info(f"✓ SUCCESS: Received {len(self.messages_received)} queries")
        else:
            logger.error(
                f"✗ FAILED: Expected {len(test_queries)} queries, "
                f"received {len(self.messages_received)}"
            )

        self.messages_received.clear()

    def test_bot_responses(self):
        """Test bot-responses topic"""
        logger.info("\n=== Testing bot-responses topic ===")

        # Create producer
        producer = RTFMKafkaProducer(self.bootstrap_servers)

        # Create consumer
        consumer = BotResponseConsumer(self.bootstrap_servers, group_id="test-group-3")

        # Define message handler
        def response_handler(response: dict):
            logger.info(f"✓ Received bot response: {response['response_text'][:50]}")
            self.messages_received.append(response)

        # Start consumer in background
        thread = consumer.consume_async(response_handler)

        # Give consumer time to connect
        time.sleep(3)

        # Send test responses
        test_responses = [
            {
                "response_id": str(uuid.uuid4()),
                "query_id": str(uuid.uuid4()),
                "original_message_id": str(uuid.uuid4()),
                "response_text": "The API endpoint is /api/v1/data. This was discussed in the chat on March 15th.",
                "channel_id": "987654321",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {"confidence": 0.95}
            },
            {
                "response_id": str(uuid.uuid4()),
                "query_id": str(uuid.uuid4()),
                "original_message_id": str(uuid.uuid4()),
                "response_text": "To configure the database, you need to set the DB_HOST and DB_PORT environment variables.",
                "channel_id": "444555666",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {"confidence": 0.88}
            }
        ]

        for response in test_responses:
            success = producer.send_bot_response(response)
            if success:
                logger.info(f"✓ Sent bot response: {response['response_text'][:50]}")
            else:
                logger.error(f"✗ Failed to send bot response")

        # Wait for messages to be consumed
        logger.info("Waiting for responses to be consumed...")
        time.sleep(5)

        # Cleanup
        consumer.stop()
        producer.close()

        # Verify
        if len(self.messages_received) >= len(test_responses):
            logger.info(f"✓ SUCCESS: Received {len(self.messages_received)} responses")
        else:
            logger.error(
                f"✗ FAILED: Expected {len(test_responses)} responses, "
                f"received {len(self.messages_received)}"
            )

        self.messages_received.clear()

    def run_all_tests(self):
        """Run all tests"""
        logger.info("Starting Kafka integration tests...\n")

        try:
            self.test_discord_messages()
            time.sleep(2)

            self.test_bot_queries()
            time.sleep(2)

            self.test_bot_responses()

            logger.info("\n=== All tests completed ===")

        except Exception as e:
            logger.error(f"Test failed with error: {e}", exc_info=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Kafka producer/consumer")
    parser.add_argument(
        "--bootstrap-servers",
        default="localhost:29092",
        help="Kafka bootstrap servers"
    )
    parser.add_argument(
        "--test",
        choices=["all", "discord", "queries", "responses"],
        default="all",
        help="Which test to run"
    )

    args = parser.parse_args()

    tester = KafkaTest(args.bootstrap_servers)

    if args.test == "all":
        tester.run_all_tests()
    elif args.test == "discord":
        tester.test_discord_messages()
    elif args.test == "queries":
        tester.test_bot_queries()
    elif args.test == "responses":
        tester.test_bot_responses()
