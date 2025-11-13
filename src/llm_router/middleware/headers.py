"""Header manipulation middleware."""

import logging
import re
from typing import Dict, List

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
        # Pre-compile regex patterns for drop_headers
        self._compiled_drop_patterns: List[re.Pattern] = []
        self._exact_drop_headers: set = set()

        for pattern in config.drop_headers:
            # Check if it's a regex pattern (contains regex special chars)
            if any(char in pattern for char in r'.*+?[]{}()^$|\\'):
                try:
                    self._compiled_drop_patterns.append(
                        re.compile(pattern, re.IGNORECASE)
                    )
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            else:
                # Exact match (case-insensitive)
                self._exact_drop_headers.add(pattern.lower())

    def _should_drop_header(self, header_name: str) -> bool:
        """Check if header should be dropped.

        Args:
            header_name: Header name to check

        Returns:
            True if header should be dropped
        """
        # Check exact matches
        if header_name.lower() in self._exact_drop_headers:
            return True

        # Check regex patterns
        for pattern in self._compiled_drop_patterns:
            if pattern.match(header_name):
                return True

        return False

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

            # Drop specified headers (supports regex)
            result = {
                k: v
                for k, v in result.items()
                if not self._should_drop_header(k)
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
