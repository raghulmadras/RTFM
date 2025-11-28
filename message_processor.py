"""
============================================================================
RTFM Discord Bot - Message Processor Service
============================================================================

This service consumes messages from Kafka and processes them:
1. Consumes from discord-messages -> stores in ChromaDB
2. Consumes from bot-queries -> generates AI responses -> produces to bot-responses
"""

import logging
import signal
import sys
from datetime import datetime
from typing import Optional
import uuid
import redis
from cache_warmer import CacheWarmer
from cache_monitor import CacheMonitor

from database import Database
from kafka_consumer import DiscordMessageConsumer, BotQueryConsumer, MultiConsumerManager
from kafka_producer import RTFMKafkaProducer
import google.generativeai as genai
import os
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Initialize cache warmer and monitor
cache_warmer = CacheWarmer(redis_client, your_vector_search_function)
cache_monitor = CacheMonitor(redis_client)

# On startup, warm the cache
async def on_startup():
    server_id = "YOUR_SERVER_ID"  # Get from config
    
    # Warm cache immediately
    cache_warmer.warm_cache_on_startup(server_id)
    
    # Start periodic refresh in background
    asyncio.create_task(cache_warmer.periodic_cache_refresh(server_id, interval_minutes=30))

# When handling search queries
def handle_search_query(query: str, server_id: str):
    query_hash = hashlib.md5(query.lower().encode()).hexdigest()
    cache_key = f"query:{server_id}:{query_hash}"
    
    # Try to get from cache
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        cache_monitor.record_hit()
        return json.loads(cached_result)
    
    # Cache miss - perform search
    cache_monitor.record_miss()
    results = perform_vector_search(query, server_id)
    
    # Store in cache
    redis_client.setex(cache_key, 3600, json.dumps(results))
    
    return results

class MessageProcessor:
    """
    Processes messages from Kafka topics

    Handles:
    - Storing Discord messages in ChromaDB
    - Processing bot queries and generating responses
    """

    def __init__(
        self,
        kafka_bootstrap_servers: str = "kafka:9092",
        gemini_api_key: Optional[str] = None
    ):
        self.db = Database()
        self.producer = RTFMKafkaProducer(kafka_bootstrap_servers)
        self.consumer_manager = MultiConsumerManager()

        # Initialize Gemini
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            logger.warning("No Gemini API key provided - AI responses disabled")

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("Shutdown signal received, stopping consumers...")
        self.stop()
        sys.exit(0)

    def process_discord_message(self, message: dict):
        """
        Process a Discord message by storing it in ChromaDB

        Args:
            message: Dictionary containing message data
        """
        try:
            logger.info(
                f"Processing Discord message from {message['username']}: "
                f"{message['content'][:50]}..."
            )

            # Store in database
            self.db.add_message(
                content=message['content'],
                username=message['username'],
                date=message['timestamp']
            )

            logger.info(f"Stored message {message['message_id']} in database")

        except Exception as e:
            logger.error(f"Error processing Discord message: {e}", exc_info=True)

    def process_bot_query(self, query: dict):
        """
        Process a bot query by generating an AI response

        Args:
            query: Dictionary containing query data
        """
        try:
            logger.info(
                f"Processing bot query from {query['username']}: "
                f"{query['question']}"
            )

            # Generate response
            response_text = self._generate_ai_response(query['question'])

            # Create response message
            response_data = {
                "response_id": str(uuid.uuid4()),
                "query_id": query['query_id'],
                "original_message_id": query['original_message_id'],
                "response_text": response_text,
                "channel_id": query['channel_id'],
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "model": "gemini-2.5-flash" if self.model else "none"
                }
            }

            # Send to bot-responses topic
            success = self.producer.send_bot_response(response_data)

            if success:
                logger.info(f"Generated and sent response for query {query['query_id']}")
            else:
                logger.error(f"Failed to send response for query {query['query_id']}")

        except Exception as e:
            logger.error(f"Error processing bot query: {e}", exc_info=True)

    def _generate_ai_response(self, question: str) -> str:
        """
        Generate AI response using ChromaDB and Gemini

        Args:
            question: User's question

        Returns:
            AI-generated response text
        """
        try:
            if not self.model:
                return "AI responses are currently disabled (no API key configured)."

            # Query the database for relevant messages
            query_results = self.db.query(
                question,
                k=10,
                min_confidence=0.3,
                max_results=5
            )

            if not query_results:
                return "I couldn't find any relevant information in the chat history to answer your question."

            # Prepare context from database results
            context = ""
            for content, metadata, confidence in query_results:
                context += f"[{metadata['date']}] {metadata['username']}: {content}\n"

            # Create prompt for Gemini
            prompt = f"""Based on the following Discord chat history, please answer the question: "{question}"

Chat History:
{context}

Please provide a helpful and accurate response based on the information available in the chat history. If the information is insufficient, say so clearly."""

            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "Sorry, I encountered an error while trying to answer your question."

    def handle_error(self, error: Exception):
        """Handle consumer errors"""
        logger.error(f"Consumer error: {error}", exc_info=True)

    def start(self, kafka_bootstrap_servers: str = "kafka:9092"):
        """Start all consumers"""
        logger.info("Starting message processor service...")

        # Add Discord message consumer
        discord_consumer = DiscordMessageConsumer(kafka_bootstrap_servers)
        self.consumer_manager.add_consumer(
            "discord-messages",
            discord_consumer,
            self.process_discord_message,
            self.handle_error
        )

        # Add bot query consumer
        query_consumer = BotQueryConsumer(kafka_bootstrap_servers)
        self.consumer_manager.add_consumer(
            "bot-queries",
            query_consumer,
            self.process_bot_query,
            self.handle_error
        )

        logger.info("Message processor service started successfully")

        # Keep the main thread alive
        try:
            while True:
                signal.pause()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.stop()

    def stop(self):
        """Stop all consumers and close connections"""
        logger.info("Stopping message processor service...")
        self.consumer_manager.stop_all()
        self.producer.close()
        logger.info("Message processor service stopped")


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    processor = MessageProcessor(
        kafka_bootstrap_servers=kafka_servers,
        gemini_api_key=gemini_api_key
    )

    processor.start(kafka_servers)
