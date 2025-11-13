"""Anthropic HTTP client."""

import logging
from typing import Any, AsyncIterator, Dict

import httpx

from .base import BaseClient

logger = logging.getLogger(__name__)


class AnthropicClient(BaseClient):
    """Anthropic API client."""

    async def create_message(
        self, data: Dict[str, Any], stream: bool = False
    ) -> httpx.Response | AsyncIterator[bytes]:
        """Create message.

        Args:
            data: Request data
            stream: Whether to stream response

        Returns:
            Response or async iterator of chunks
        """
        if stream:
            return self._stream_request("POST", "/v1/messages", data)
        else:
            return await self._make_request("POST", "/v1/messages", data)
