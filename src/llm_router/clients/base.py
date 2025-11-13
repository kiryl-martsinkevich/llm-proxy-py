"""Base HTTP client with retry and header manipulation."""

import logging
from typing import Any, AsyncIterator, Dict, Optional

import httpx

from ..config import ModelConfig, RetryConfig
from ..middleware.headers import HeaderManipulator
from ..middleware.logging import RequestLogger
from ..middleware.transform import ContentTransformer
from ..utils.retry import RetryHandler

logger = logging.getLogger(__name__)


class BaseClient:
    """Base HTTP client for LLM providers."""

    def __init__(
        self,
        model_config: ModelConfig,
        retry_config: RetryConfig,
        header_manipulator: HeaderManipulator,
        content_transformer: ContentTransformer,
        request_logger: Optional[RequestLogger] = None,
        log_requests: bool = False,
        log_responses: bool = False,
    ):
        """Initialize base client.

        Args:
            model_config: Model configuration
            retry_config: Retry configuration
            header_manipulator: Header manipulator
            content_transformer: Content transformer
            request_logger: Request logger
            log_requests: Whether to log requests
            log_responses: Whether to log responses
        """
        self.model_config = model_config
        self.retry_handler = RetryHandler(retry_config)
        self.header_manipulator = header_manipulator
        self.content_transformer = content_transformer
        self.request_logger = request_logger
        self.log_requests = log_requests
        self.log_responses = log_responses

        # Create HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=model_config.connect_timeout,
                read=model_config.timeout,
                write=model_config.timeout,
                pool=5.0,
            ),
            verify=model_config.ssl_verify,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    def _prepare_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare headers for request.

        Args:
            additional_headers: Additional headers to include

        Returns:
            Processed headers
        """
        headers = {
            "content-type": "application/json",
        }

        # Add API key if configured
        if self.model_config.api_key:
            if "anthropic" in self.model_config.provider.lower():
                headers["x-api-key"] = self.model_config.api_key
                headers["anthropic-version"] = "2023-06-01"
            else:
                headers["authorization"] = f"Bearer {self.model_config.api_key}"

        # Add any additional headers
        if additional_headers:
            headers.update(additional_headers)

        # Apply header manipulation
        return self.header_manipulator.process_headers(headers)

    def _transform_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform request data.

        Args:
            data: Original request data

        Returns:
            Transformed request data
        """
        return self.content_transformer.transform_request(data)

    async def _make_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method
            path: API path
            data: Request data
            headers: Additional headers

        Returns:
            HTTP response
        """
        url = f"{self.model_config.endpoint.rstrip('/')}/{path.lstrip('/')}"
        prepared_headers = self._prepare_headers(headers)

        # Transform request data
        if data:
            data = self._transform_request(data)

        # Log request if enabled
        if self.log_requests and self.request_logger:
            self.request_logger.log_request(method, url, prepared_headers, data)

        async def _request():
            return await self.client.request(
                method=method,
                url=url,
                json=data,
                headers=prepared_headers,
            )

        # Execute with retry
        response = await self.retry_handler.execute_with_retry(
            _request,
            operation_name=f"{method} {path}",
        )

        # Log response if enabled
        if self.log_responses and self.request_logger:
            try:
                response_data = response.json()
            except Exception:
                response_data = response.text

            self.request_logger.log_response(
                response.status_code,
                dict(response.headers),
                response_data,
            )

        return response

    async def _stream_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> AsyncIterator[bytes]:
        """Make streaming HTTP request.

        Args:
            method: HTTP method
            path: API path
            data: Request data
            headers: Additional headers

        Yields:
            Response chunks
        """
        url = f"{self.model_config.endpoint.rstrip('/')}/{path.lstrip('/')}"
        prepared_headers = self._prepare_headers(headers)

        # Transform request data
        if data:
            data = self._transform_request(data)

        # Log request if enabled
        if self.log_requests and self.request_logger:
            self.request_logger.log_request(method, url, prepared_headers, data)

        try:
            async with self.client.stream(
                method=method,
                url=url,
                json=data,
                headers=prepared_headers,
            ) as response:
                response.raise_for_status()

                async for chunk in response.aiter_bytes():
                    yield chunk

        except Exception as e:
            if self.request_logger:
                self.request_logger.log_error(e, context="streaming request")
            raise
