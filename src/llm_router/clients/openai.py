"""OpenAI HTTP client."""

import logging
from typing import Any, AsyncIterator, Dict

import httpx

from .base import BaseClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseClient):
    """OpenAI API client."""

    async def chat_completion(
        self, data: Dict[str, Any], stream: bool = False
    ) -> httpx.Response | AsyncIterator[bytes]:
        """Create chat completion.

        Args:
            data: Request data
            stream: Whether to stream response

        Returns:
            Response or async iterator of chunks
        """
        if stream:
            return self._stream_request("POST", "/v1/chat/completions", data)
        else:
            return await self._make_request("POST", "/v1/chat/completions", data)

    async def completion(
        self, data: Dict[str, Any], stream: bool = False
    ) -> httpx.Response | AsyncIterator[bytes]:
        """Create completion.

        Args:
            data: Request data
            stream: Whether to stream response

        Returns:
            Response or async iterator of chunks
        """
        if stream:
            return self._stream_request("POST", "/v1/completions", data)
        else:
            return await self._make_request("POST", "/v1/completions", data)
