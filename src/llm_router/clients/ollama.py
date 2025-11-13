"""Ollama HTTP client."""

import logging
from typing import Any, AsyncIterator, Dict

import httpx

from .base import BaseClient

logger = logging.getLogger(__name__)


class OllamaClient(BaseClient):
    """Ollama API client."""

    async def generate(
        self, data: Dict[str, Any], stream: bool = False
    ) -> httpx.Response | AsyncIterator[bytes]:
        """Generate completion.

        Args:
            data: Request data
            stream: Whether to stream response

        Returns:
            Response or async iterator of chunks
        """
        if stream:
            return self._stream_request("POST", "/api/generate", data)
        else:
            return await self._make_request("POST", "/api/generate", data)

    async def chat(
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
            return self._stream_request("POST", "/api/chat", data)
        else:
            return await self._make_request("POST", "/api/chat", data)

    async def chat_completion(
        self, data: Dict[str, Any], stream: bool = False
    ) -> httpx.Response | AsyncIterator[bytes]:
        """Create chat completion (OpenAI-compatible wrapper).

        This method wraps the Ollama chat endpoint to provide an OpenAI-compatible
        interface for the router.

        Args:
            data: Request data (OpenAI format)
            stream: Whether to stream response

        Returns:
            Response or async iterator of chunks
        """
        return await self.chat(data, stream)

    async def completion(
        self, data: Dict[str, Any], stream: bool = False
    ) -> httpx.Response | AsyncIterator[bytes]:
        """Create text completion (OpenAI-compatible wrapper).

        This method wraps the Ollama generate endpoint to provide an OpenAI-compatible
        interface for the router.

        Args:
            data: Request data (OpenAI format)
            stream: Whether to stream response

        Returns:
            Response or async iterator of chunks
        """
        return await self.generate(data, stream)
