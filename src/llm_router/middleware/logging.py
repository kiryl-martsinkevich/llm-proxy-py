"""Request and response logging middleware."""

import json
import logging
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)


class RequestLogger:
    """Handles request and response logging with sensitive data masking."""

    def __init__(self, mask_api_keys: bool = True):
        """Initialize request logger.

        Args:
            mask_api_keys: Whether to mask API keys in logs
        """
        self.mask_api_keys = mask_api_keys
        self._api_key_pattern = re.compile(
            r"(sk-[a-zA-Z0-9]{20,}|sk-ant-[a-zA-Z0-9-]{20,})",
            re.IGNORECASE,
        )

    def mask_sensitive_data(self, text: str) -> str:
        """Mask sensitive data in text.

        Args:
            text: Text to mask

        Returns:
            Masked text
        """
        if not self.mask_api_keys:
            return text

        # Mask API keys
        text = self._api_key_pattern.sub(lambda m: m.group(0)[:8] + "..." + m.group(0)[-4:], text)

        return text

    def mask_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Mask sensitive headers.

        Args:
            headers: Original headers

        Returns:
            Headers with masked values
        """
        if not self.mask_api_keys:
            return headers

        masked = {}
        sensitive_headers = {"authorization", "x-api-key", "api-key", "apikey"}

        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                # Mask the value
                if len(value) > 12:
                    masked[key] = value[:8] + "..." + value[-4:]
                else:
                    masked[key] = "***"
            else:
                masked[key] = value

        return masked

    def log_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Any = None,
    ) -> None:
        """Log outgoing request.

        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body
        """
        masked_headers = self.mask_headers(headers)

        log_data = {
            "type": "request",
            "method": method,
            "url": url,
            "headers": masked_headers,
        }

        if body is not None:
            if isinstance(body, (dict, list)):
                body_str = json.dumps(body)
            else:
                body_str = str(body)

            log_data["body"] = self.mask_sensitive_data(body_str)

        logger.info(f"Request: {json.dumps(log_data, indent=2)}")

    def log_response(
        self,
        status_code: int,
        headers: Dict[str, str],
        body: Any = None,
    ) -> None:
        """Log incoming response.

        Args:
            status_code: HTTP status code
            headers: Response headers
            body: Response body
        """
        masked_headers = self.mask_headers(headers)

        log_data = {
            "type": "response",
            "status_code": status_code,
            "headers": masked_headers,
        }

        if body is not None:
            if isinstance(body, (dict, list)):
                body_str = json.dumps(body)
            else:
                body_str = str(body)

            log_data["body"] = self.mask_sensitive_data(body_str)

        logger.info(f"Response: {json.dumps(log_data, indent=2)}")

    def log_error(
        self,
        error: Exception,
        context: str = "request",
    ) -> None:
        """Log error with context.

        Args:
            error: Exception that occurred
            context: Context description
        """
        logger.error(
            f"Error during {context}: {type(error).__name__}: {str(error)}",
            exc_info=True,
        )
