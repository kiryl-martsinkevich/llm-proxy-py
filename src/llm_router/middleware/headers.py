"""Header manipulation middleware."""

import logging
from typing import Dict

from ..config import HeaderRuleConfig

logger = logging.getLogger(__name__)


class HeaderManipulator:
    """Handles header manipulation for requests."""

    def __init__(self, config: HeaderRuleConfig):
        """Initialize header manipulator.

        Args:
            config: Header rule configuration
        """
        self.config = config

    def process_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Process headers according to configuration.

        Args:
            headers: Original headers

        Returns:
            Processed headers
        """
        if self.config.drop_all:
            # Start with empty dict, only use configured headers
            result = {}
        else:
            # Start with original headers
            result = dict(headers)

            # Drop specified headers (case-insensitive)
            drop_headers_lower = {h.lower() for h in self.config.drop_headers}
            result = {
                k: v
                for k, v in result.items()
                if k.lower() not in drop_headers_lower
            }

        # Add new headers (don't override if exists)
        for key, value in self.config.add_headers.items():
            if key not in result:
                result[key] = value

        # Force headers (override if exists)
        for key, value in self.config.force_headers.items():
            result[key] = value

        logger.debug(f"Processed headers: {len(headers)} -> {len(result)}")
        return result

    def get_default_headers(self) -> Dict[str, str]:
        """Get default headers from configuration.

        Returns:
            Dict of default headers
        """
        headers = {}
        headers.update(self.config.add_headers)
        headers.update(self.config.force_headers)
        return headers
