"""
============================================================================
RTFM Discord Bot - Kafka Message Schemas
============================================================================

This module defines the JSON schemas for messages passed through Kafka topics:
- discord-messages: Raw messages from Discord
- bot-queries: User queries that need AI responses
- bot-responses: AI-generated responses to be sent to Discord
"""

from typing import TypedDict, Optional
from datetime import datetime
import json


class DiscordMessage(TypedDict):
    """
    Schema for discord-messages topic

    Represents a raw Discord message that needs to be stored in the database.
    """
    message_id: str
    content: str
    username: str
    user_id: str
    channel_id: str
    timestamp: str  # ISO 8601 format
    metadata: Optional[dict]


class BotQuery(TypedDict):
    """
    Schema for bot-queries topic

    Represents a user query that triggered the bot and needs an AI response.
    """
    query_id: str
    original_message_id: str
    question: str
    username: str
    user_id: str
    channel_id: str
    timestamp: str  # ISO 8601 format
    context: Optional[dict]


class BotResponse(TypedDict):
    """
    Schema for bot-responses topic

    Represents an AI-generated response ready to be sent to Discord.
    """
    response_id: str
    query_id: str
    original_message_id: str
    response_text: str
    channel_id: str
    timestamp: str  # ISO 8601 format
    metadata: Optional[dict]


class SchemaValidator:
    """Validates and serializes/deserializes Kafka messages"""

    @staticmethod
    def serialize_discord_message(
        message_id: str,
        content: str,
        username: str,
        user_id: str,
        channel_id: str,
        timestamp: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """Serialize a Discord message to JSON string"""
        message: DiscordMessage = {
            "message_id": message_id,
            "content": content,
            "username": username,
            "user_id": user_id,
            "channel_id": channel_id,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        return json.dumps(message)

    @staticmethod
    def serialize_bot_query(
        query_id: str,
        original_message_id: str,
        question: str,
        username: str,
        user_id: str,
        channel_id: str,
        timestamp: Optional[str] = None,
        context: Optional[dict] = None
    ) -> str:
        """Serialize a bot query to JSON string"""
        query: BotQuery = {
            "query_id": query_id,
            "original_message_id": original_message_id,
            "question": question,
            "username": username,
            "user_id": user_id,
            "channel_id": channel_id,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "context": context or {}
        }
        return json.dumps(query)

    @staticmethod
    def serialize_bot_response(
        response_id: str,
        query_id: str,
        original_message_id: str,
        response_text: str,
        channel_id: str,
        timestamp: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """Serialize a bot response to JSON string"""
        response: BotResponse = {
            "response_id": response_id,
            "query_id": query_id,
            "original_message_id": original_message_id,
            "response_text": response_text,
            "channel_id": channel_id,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        return json.dumps(response)

    @staticmethod
    def deserialize_discord_message(json_str: str) -> DiscordMessage:
        """Deserialize a Discord message from JSON string"""
        return json.loads(json_str)

    @staticmethod
    def deserialize_bot_query(json_str: str) -> BotQuery:
        """Deserialize a bot query from JSON string"""
        return json.loads(json_str)

    @staticmethod
    def deserialize_bot_response(json_str: str) -> BotResponse:
        """Deserialize a bot response from JSON string"""
        return json.loads(json_str)


# Example message formats for documentation
EXAMPLE_DISCORD_MESSAGE = {
    "message_id": "1234567890",
    "content": "RTFM what is the API endpoint?",
    "username": "user#1234",
    "user_id": "987654321",
    "channel_id": "111222333",
    "timestamp": "2025-11-02T12:34:56.789Z",
    "metadata": {}
}

EXAMPLE_BOT_QUERY = {
    "query_id": "query_abc123",
    "original_message_id": "1234567890",
    "question": "what is the API endpoint?",
    "username": "user#1234",
    "user_id": "987654321",
    "channel_id": "111222333",
    "timestamp": "2025-11-02T12:34:56.789Z",
    "context": {}
}

EXAMPLE_BOT_RESPONSE = {
    "response_id": "response_xyz789",
    "query_id": "query_abc123",
    "original_message_id": "1234567890",
    "response_text": "The API endpoint is /api/v1/data",
    "channel_id": "111222333",
    "timestamp": "2025-11-02T12:34:57.123Z",
    "metadata": {
        "confidence": 0.95,
        "sources_count": 3
    }
}
