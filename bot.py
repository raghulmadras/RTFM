import os
import discord
from datetime import datetime
from dotenv import load_dotenv
import asyncio
import uuid
import logging
from kafka_producer import RTFMKafkaProducer
from kafka_consumer import BotResponseConsumer
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DiscordRTFMBot:
    TRIGGER_PHRASE = ["rtfm", "RTFM", "Rtfm", "Read The F***ing Manual"]


    def __init__(self, bot_token, kafka_bootstrap_servers="kafka:9092"):
        # Load tokens
        self.BOT_TOKEN = bot_token

        # Initialize Kafka producer
        self.kafka_producer = RTFMKafkaProducer(kafka_bootstrap_servers)

        # Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)

        # Channel references for sending responses
        self.channels = {}

        # Pending queries (to track responses)
        self.pending_queries = {}

        # Start response consumer in background
        self.response_consumer = BotResponseConsumer(kafka_bootstrap_servers)
        self.response_thread = self.response_consumer.consume_async(
            self.handle_bot_response,
            self.handle_consumer_error
        )

        # Register events
        self.client.event(self.on_ready)
        self.client.event(self.on_message)


    def handle_bot_response(self, response: dict):
        """
        Handle bot responses from Kafka

        This is called by the Kafka consumer when a response is ready.
        """
        try:
            channel_id = int(response['channel_id'])
            response_text = response['response_text']

            logger.info(f"Received response for channel {channel_id}")

            # Schedule sending the message in the Discord event loop
            asyncio.run_coroutine_threadsafe(
                self._send_response(channel_id, response_text),
                self.client.loop
            )

        except Exception as e:
            logger.error(f"Error handling bot response: {e}", exc_info=True)

    async def _send_response(self, channel_id: int, response_text: str):
        """
        Send a response to a Discord channel

        Args:
            channel_id: Discord channel ID
            response_text: Response text to send
        """
        try:
            channel = self.client.get_channel(channel_id)
            if channel:
                await channel.send(response_text)
                logger.info(f"Sent response to channel {channel_id}")
            else:
                logger.error(f"Channel {channel_id} not found")
        except Exception as e:
            logger.error(f"Error sending response to channel {channel_id}: {e}")

    def handle_consumer_error(self, error: Exception):
        """Handle errors from the Kafka consumer"""
        logger.error(f"Kafka consumer error: {error}", exc_info=True)


    async def on_ready(self):
        logger.info(f'Logged in as {self.client.user}')


    async def on_message(self, message):
        if message.author == self.client.user:
            return

        try:
            # Get message details
            message_creation_time = message.created_at
            formatted_time = message_creation_time.isoformat()

            # Send message to discord-messages topic
            message_data = {
                "message_id": str(message.id),
                "content": message.content,
                "username": str(message.author),
                "user_id": str(message.author.id),
                "channel_id": str(message.channel.id),
                "timestamp": formatted_time,
                "metadata": {
                    "channel_name": message.channel.name if hasattr(message.channel, 'name') else "DM"
                }
            }

            self.kafka_producer.send_discord_message(message_data)
            logger.info(
                f"[{formatted_time}] [{message.channel}] {message.author}: "
                f"{message.content[:50]}..."
            )

            # Check for trigger phrase
            if any(phrase.lower() in message.content.lower() for phrase in self.TRIGGER_PHRASE):
                logger.info(f"Trigger phrase detected in message: {message.content}")

                # Remove trigger phrase to extract question
                question = message.content
                for phrase in self.TRIGGER_PHRASE:
                    question = question.replace(phrase, "").strip()

                if question:
                    # Send query to bot-queries topic
                    query_id = str(uuid.uuid4())
                    query_data = {
                        "query_id": query_id,
                        "original_message_id": str(message.id),
                        "question": question,
                        "username": str(message.author),
                        "user_id": str(message.author.id),
                        "channel_id": str(message.channel.id),
                        "timestamp": datetime.utcnow().isoformat(),
                        "context": {}
                    }

                    self.kafka_producer.send_bot_query(query_data)
                    logger.info(f"Sent query to Kafka: {question}")

                else:
                    await message.channel.send(
                        "Please ask a specific question after the trigger phrase so I can help you find relevant information from the chat history."
                    )

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)


    def run(self):
        try:
            self.client.run(self.BOT_TOKEN)
        finally:
            # Cleanup
            self.response_consumer.stop()
            self.kafka_producer.close()
            logger.info("Bot shutdown complete")


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    BOT_TOKEN = os.getenv("DISCORD_TOKEN")
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    bot = DiscordRTFMBot(BOT_TOKEN, KAFKA_BOOTSTRAP_SERVERS)
    bot.run()

