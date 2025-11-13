"""Retry logic for HTTP requests."""

import asyncio
import logging
from typing import Callable, Optional, TypeVar

import httpx

from ..config import RetryConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryHandler:
    """Handles retry logic for HTTP requests with exponential backoff."""

    def __init__(self, config: RetryConfig):
        """Initialize retry handler.

        Args:
            config: Retry configuration
        """
        self.config = config

    def should_retry(self, response: Optional[httpx.Response], exception: Optional[Exception]) -> bool:
        """Determine if request should be retried.

        Args:
            response: HTTP response if available
            exception: Exception if raised

        Returns:
            True if should retry, False otherwise
        """
        # Retry on specific HTTP status codes
        if response is not None:
            return response.status_code in self.config.retry_status_codes

        # Retry on network errors
        if isinstance(exception, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)):
            return True

        return False

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt with exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = self.config.initial_delay * (self.config.backoff_factor ** attempt)
        return min(delay, self.config.max_delay)

    async def execute_with_retry(
        self,
        func: Callable[[], T],
        operation_name: str = "request",
    ) -> T:
        """Execute function with retry logic.

        Args:
            func: Async function to execute
            operation_name: Name of operation for logging

        Returns:
            Result from function

        Raises:
            Last exception encountered if all retries fail
        """
        last_exception: Optional[Exception] = None
        last_response: Optional[httpx.Response] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                result = await func()

                # If result is an httpx.Response, check if we should retry
                if isinstance(result, httpx.Response):
                    if not self.should_retry(result, None):
                        return result

                    last_response = result
                    if attempt < self.config.max_retries:
                        delay = self.calculate_delay(attempt)
                        logger.warning(
                            f"{operation_name} returned {result.status_code}, "
                            f"retrying in {delay:.2f}s (attempt {attempt + 1}/{self.config.max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue
                else:
                    return result

            except Exception as e:
                last_exception = e

                if not self.should_retry(None, e):
                    raise

                if attempt < self.config.max_retries:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"{operation_name} failed with {type(e).__name__}: {e}, "
                        f"retrying in {delay:.2f}s (attempt {attempt + 1}/{self.config.max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise

        # All retries exhausted
        if last_response:
            logger.error(
                f"{operation_name} failed after {self.config.max_retries} retries, "
                f"last status: {last_response.status_code}"
            )
            return last_response

        if last_exception:
            logger.error(
                f"{operation_name} failed after {self.config.max_retries} retries, "
                f"last error: {last_exception}"
            )
            raise last_exception

        raise RuntimeError(f"{operation_name} failed with unknown error")
