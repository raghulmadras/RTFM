"""
============================================================================
RTFM Discord Bot - Kafka Topic Initialization
============================================================================

This script creates the required Kafka topics for the RTFM bot.

Topics:
- discord-messages: Raw Discord messages to be stored in the database
- bot-queries: User queries that need AI responses
- bot-responses: AI-generated responses to send back to Discord
"""

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, KafkaError
import logging
import sys
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_topics(bootstrap_servers: str = "kafka:9092", retries: int = 5):
    """
    Create the required Kafka topics

    Args:
        bootstrap_servers: Kafka broker address
        retries: Number of connection retries
    """

    # Define topics
    topics = [
        NewTopic(
            name="discord-messages",
            num_partitions=3,
            replication_factor=1,
            topic_configs={
                "retention.ms": "604800000",  # 7 days
                "cleanup.policy": "delete"
            }
        ),
        NewTopic(
            name="bot-queries",
            num_partitions=3,
            replication_factor=1,
            topic_configs={
                "retention.ms": "86400000",  # 1 day
                "cleanup.policy": "delete"
            }
        ),
        NewTopic(
            name="bot-responses",
            num_partitions=3,
            replication_factor=1,
            topic_configs={
                "retention.ms": "86400000",  # 1 day
                "cleanup.policy": "delete"
            }
        )
    ]

    # Try to connect with retries
    admin_client = None
    for attempt in range(retries):
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=bootstrap_servers,
                client_id="topic-initializer"
            )
            logger.info(f"Connected to Kafka at {bootstrap_servers}")
            break
        except KafkaError as e:
            if attempt < retries - 1:
                logger.warning(
                    f"Failed to connect to Kafka (attempt {attempt + 1}/{retries}): {e}"
                )
                time.sleep(5)
            else:
                logger.error(f"Could not connect to Kafka after {retries} attempts")
                sys.exit(1)

    # Create topics
    try:
        result = admin_client.create_topics(
            new_topics=topics,
            validate_only=False
        )

        # Check results
        for topic, future in result.items():
            try:
                future.result()  # Block until topic is created
                logger.info(f"✓ Topic '{topic}' created successfully")
            except TopicAlreadyExistsError:
                logger.info(f"✓ Topic '{topic}' already exists")
            except Exception as e:
                logger.error(f"✗ Failed to create topic '{topic}': {e}")

    except Exception as e:
        logger.error(f"Error creating topics: {e}")
        sys.exit(1)
    finally:
        if admin_client:
            admin_client.close()

    logger.info("Topic initialization complete")


def list_topics(bootstrap_servers: str = "kafka:9092"):
    """
    List all Kafka topics

    Args:
        bootstrap_servers: Kafka broker address
    """
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            client_id="topic-lister"
        )

        topics = admin_client.list_topics()
        logger.info("Existing topics:")
        for topic in topics:
            logger.info(f"  - {topic}")

        admin_client.close()
    except Exception as e:
        logger.error(f"Error listing topics: {e}")


def delete_topics(bootstrap_servers: str = "kafka:9092"):
    """
    Delete RTFM topics (for cleanup/reset)

    Args:
        bootstrap_servers: Kafka broker address
    """
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            client_id="topic-deleter"
        )

        topics_to_delete = [
            "discord-messages",
            "bot-queries",
            "bot-responses"
        ]

        result = admin_client.delete_topics(topics_to_delete)

        for topic, future in result.items():
            try:
                future.result()
                logger.info(f"✓ Topic '{topic}' deleted")
            except Exception as e:
                logger.warning(f"Could not delete topic '{topic}': {e}")

        admin_client.close()
    except Exception as e:
        logger.error(f"Error deleting topics: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage Kafka topics for RTFM bot")
    parser.add_argument(
        "--action",
        choices=["create", "list", "delete"],
        default="create",
        help="Action to perform"
    )
    parser.add_argument(
        "--bootstrap-servers",
        default="localhost:29092",
        help="Kafka bootstrap servers (default: localhost:29092)"
    )

    args = parser.parse_args()

    if args.action == "create":
        create_topics(args.bootstrap_servers)
    elif args.action == "list":
        list_topics(args.bootstrap_servers)
    elif args.action == "delete":
        delete_topics(args.bootstrap_servers)
