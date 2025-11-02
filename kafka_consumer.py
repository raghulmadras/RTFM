"""
============================================================================
RTFM Discord Bot - Kafka Consumers
============================================================================

This module handles consuming messages from Kafka topics and processing them.
"""

from kafka import KafkaConsumer
from kafka.errors import KafkaError
import json
import logging
from typing import Callable, Optional, Dict
import threading

logger = logging.getLogger(__name__)


class RTFMKafkaConsumer:
    """
    Base Kafka consumer for RTFM bot

    Handles consuming messages from a specific topic and processing them
    with a callback function.
    """

    def __init__(
        self,
        topic: str,
        group_id: str,
        bootstrap_servers: str = "kafka:9092",
        auto_offset_reset: str = "latest"
    ):
        """
        Initialize Kafka consumer

        Args:
            topic: Kafka topic to consume from
            group_id: Consumer group ID
            bootstrap_servers: Kafka broker address
            auto_offset_reset: Where to start reading ('earliest' or 'latest')
        """
        self.topic = topic
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers
        self.consumer = None
        self.running = False
        self._connect(auto_offset_reset)

    def _connect(self, auto_offset_reset: str):
        """Establish connection to Kafka broker"""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset=auto_offset_reset,
                enable_auto_commit=True,
                auto_commit_interval_ms=1000
            )
            logger.info(
                f"Connected to Kafka topic '{self.topic}' "
                f"with group '{self.group_id}'"
            )
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    def consume(
        self,
        callback: Callable[[dict], None],
        error_callback: Optional[Callable[[Exception], None]] = None
    ):
        """
        Start consuming messages and process them with callback

        Args:
            callback: Function to call for each message (receives message dict)
            error_callback: Optional function to call on errors
        """
        self.running = True
        logger.info(f"Starting to consume from topic '{self.topic}'")

        try:
            for message in self.consumer:
                if not self.running:
                    break

                try:
                    logger.debug(
                        f"Received message from {self.topic} "
                        f"[partition: {message.partition}, offset: {message.offset}]"
                    )
                    callback(message.value)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    if error_callback:
                        error_callback(e)
        except KafkaError as e:
            logger.error(f"Kafka error while consuming: {e}")
            if error_callback:
                error_callback(e)
        finally:
            self.stop()

    def consume_async(
        self,
        callback: Callable[[dict], None],
        error_callback: Optional[Callable[[Exception], None]] = None
    ) -> threading.Thread:
        """
        Start consuming messages asynchronously in a separate thread

        Args:
            callback: Function to call for each message
            error_callback: Optional function to call on errors

        Returns:
            Thread object running the consumer
        """
        thread = threading.Thread(
            target=self.consume,
            args=(callback, error_callback),
            daemon=True
        )
        thread.start()
        logger.info(f"Started async consumer thread for topic '{self.topic}'")
        return thread

    def stop(self):
        """Stop consuming messages"""
        self.running = False
        if self.consumer:
            self.consumer.close()
            logger.info(f"Kafka consumer for '{self.topic}' closed")


class DiscordMessageConsumer(RTFMKafkaConsumer):
    """Consumer for discord-messages topic"""

    def __init__(
        self,
        bootstrap_servers: str = "kafka:9092",
        group_id: str = "discord-message-processor"
    ):
        super().__init__(
            topic="discord-messages",
            group_id=group_id,
            bootstrap_servers=bootstrap_servers
        )


class BotQueryConsumer(RTFMKafkaConsumer):
    """Consumer for bot-queries topic"""

    def __init__(
        self,
        bootstrap_servers: str = "kafka:9092",
        group_id: str = "bot-query-processor"
    ):
        super().__init__(
            topic="bot-queries",
            group_id=group_id,
            bootstrap_servers=bootstrap_servers
        )


class BotResponseConsumer(RTFMKafkaConsumer):
    """Consumer for bot-responses topic"""

    def __init__(
        self,
        bootstrap_servers: str = "kafka:9092",
        group_id: str = "bot-response-sender"
    ):
        super().__init__(
            topic="bot-responses",
            group_id=group_id,
            bootstrap_servers=bootstrap_servers
        )


class MultiConsumerManager:
    """
    Manages multiple Kafka consumers

    Useful for running multiple consumers in the same process.
    """

    def __init__(self):
        self.consumers: Dict[str, RTFMKafkaConsumer] = {}
        self.threads: Dict[str, threading.Thread] = {}

    def add_consumer(
        self,
        name: str,
        consumer: RTFMKafkaConsumer,
        callback: Callable[[dict], None],
        error_callback: Optional[Callable[[Exception], None]] = None
    ):
        """
        Add and start a consumer

        Args:
            name: Unique name for this consumer
            consumer: RTFMKafkaConsumer instance
            callback: Message processing callback
            error_callback: Optional error handling callback
        """
        self.consumers[name] = consumer
        thread = consumer.consume_async(callback, error_callback)
        self.threads[name] = thread
        logger.info(f"Added consumer '{name}'")

    def stop_all(self):
        """Stop all consumers"""
        for name, consumer in self.consumers.items():
            consumer.stop()
            logger.info(f"Stopped consumer '{name}'")

        # Wait for threads to finish
        for name, thread in self.threads.items():
            thread.join(timeout=5)
            logger.info(f"Consumer thread '{name}' joined")

    def is_running(self, name: str) -> bool:
        """Check if a consumer is running"""
        return name in self.threads and self.threads[name].is_alive()


if __name__ == "__main__":
    # Test the consumer
    logging.basicConfig(level=logging.INFO)

    def message_handler(message: dict):
        print(f"Received message: {message}")

    def error_handler(error: Exception):
        print(f"Error occurred: {error}")

    consumer = DiscordMessageConsumer(bootstrap_servers="localhost:29092")

    print("Starting consumer... (Press Ctrl+C to stop)")
    try:
        consumer.consume(message_handler, error_handler)
    except KeyboardInterrupt:
        print("\nStopping consumer...")
        consumer.stop()
