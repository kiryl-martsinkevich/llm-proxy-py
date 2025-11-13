"""Streaming utilities for SSE responses."""

import json
import logging
from typing import AsyncIterator

logger = logging.getLogger(__name__)


async def stream_response(
    response_iter: AsyncIterator[bytes],
    provider: str = "unknown",
) -> AsyncIterator[str]:
    """Stream response from provider and format as SSE.

    Args:
        response_iter: Async iterator of response bytes
        provider: Provider name for logging

    Yields:
        SSE formatted strings
    """
    try:
        async for chunk in response_iter:
            if not chunk:
                continue

            # Decode bytes to string
            try:
                text = chunk.decode("utf-8")
            except UnicodeDecodeError:
                logger.warning(f"Failed to decode chunk from {provider}")
                continue

            # Yield the chunk as-is (provider format is already SSE)
            yield text

    except Exception as e:
        logger.error(f"Error streaming from {provider}: {e}")
        # Send error event
        error_data = json.dumps({
            "error": {
                "message": f"Streaming error: {str(e)}",
                "type": "stream_error",
            }
        })
        yield f"data: {error_data}\n\n"


def format_sse_event(data: str, event: str = None) -> str:
    """Format data as SSE event.

    Args:
        data: Data to send
        event: Optional event type

    Returns:
        SSE formatted string
    """
    lines = []
    if event:
        lines.append(f"event: {event}")
    lines.append(f"data: {data}")
    lines.append("")
    return "\n".join(lines)


def parse_sse_line(line: str) -> tuple[str, str]:
    """Parse SSE line into field and value.

    Args:
        line: SSE line

    Returns:
        Tuple of (field, value)
    """
    if ":" not in line:
        return "", ""

    field, _, value = line.partition(":")
    return field.strip(), value.lstrip()
