"""Content transformation middleware for request/response manipulation."""

import json
import logging
import re
from typing import Any, Dict, List

from jsonpath_ng import parse as jsonpath_parse

from ..config import TransformationConfig

logger = logging.getLogger(__name__)


class ContentTransformer:
    """Handles content transformation for requests and responses."""

    def __init__(self, transformations: List[TransformationConfig]):
        """Initialize content transformer.

        Args:
            transformations: List of transformation configurations
        """
        self.transformations = [t for t in transformations if t.enabled]
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        for transformation in self.transformations:
            if transformation.type == "regex_replace" and transformation.pattern:
                flags = 0
                if transformation.flags:
                    flag_map = {
                        "IGNORECASE": re.IGNORECASE,
                        "MULTILINE": re.MULTILINE,
                        "DOTALL": re.DOTALL,
                    }
                    for flag_name in transformation.flags.split("|"):
                        flags |= flag_map.get(flag_name.strip(), 0)

                transformation._compiled_pattern = re.compile(
                    transformation.pattern, flags
                )

    def transform_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply transformations to request data.

        Args:
            data: Request data

        Returns:
            Transformed request data
        """
        result = data.copy()

        for transformation in self.transformations:
            try:
                if transformation.type == "regex_replace":
                    result = self._apply_regex_replace(result, transformation)
                elif transformation.type == "jsonpath_drop":
                    result = self._apply_jsonpath_drop(result, transformation)
                elif transformation.type == "jsonpath_add":
                    result = self._apply_jsonpath_add(result, transformation)
                else:
                    logger.warning(f"Unknown transformation type: {transformation.type}")
            except Exception as e:
                logger.error(
                    f"Error applying transformation '{transformation.name}': {e}",
                    exc_info=True,
                )

        return result

    def _apply_regex_replace(
        self, data: Dict[str, Any], config: TransformationConfig
    ) -> Dict[str, Any]:
        """Apply regex replace transformation.

        Args:
            data: Data to transform
            config: Transformation configuration

        Returns:
            Transformed data
        """
        if not hasattr(config, "_compiled_pattern"):
            logger.warning(f"Pattern not compiled for {config.name}")
            return data

        # Convert to JSON string, apply regex, convert back
        json_str = json.dumps(data)
        transformed_str = config._compiled_pattern.sub(
            config.replacement or "", json_str
        )

        try:
            return json.loads(transformed_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON after regex replace: {e}")
            return data

    def _apply_jsonpath_drop(
        self, data: Dict[str, Any], config: TransformationConfig
    ) -> Dict[str, Any]:
        """Apply JSON path drop transformation.

        Args:
            data: Data to transform
            config: Transformation configuration

        Returns:
            Transformed data
        """
        if not config.path:
            return data

        try:
            jsonpath_expr = jsonpath_parse(config.path)
            matches = jsonpath_expr.find(data)

            if not matches:
                logger.debug(f"No matches found for path: {config.path}")
                return data

            # Work with a copy
            result = json.loads(json.dumps(data))

            # Sort matches by path depth (deepest first) to avoid index issues
            matches = sorted(matches, key=lambda m: len(str(m.full_path)), reverse=True)

            for match in matches:
                # Get parent and remove the matched element
                path_parts = str(match.full_path).split(".")

                if len(path_parts) == 1:
                    # Top-level key
                    if path_parts[0] in result:
                        del result[path_parts[0]]
                else:
                    # Nested key
                    parent = result
                    for part in path_parts[:-1]:
                        # Handle array indices
                        if part.startswith("[") and part.endswith("]"):
                            idx = int(part[1:-1])
                            parent = parent[idx]
                        else:
                            parent = parent.get(part, {})

                    last_part = path_parts[-1]
                    if isinstance(parent, dict) and last_part in parent:
                        del parent[last_part]
                    elif isinstance(parent, list):
                        # Handle list index
                        if last_part.startswith("[") and last_part.endswith("]"):
                            idx = int(last_part[1:-1])
                            if 0 <= idx < len(parent):
                                parent.pop(idx)

            logger.debug(f"Dropped {len(matches)} matches for path: {config.path}")
            return result

        except Exception as e:
            logger.error(f"Error applying jsonpath_drop: {e}", exc_info=True)
            return data

    def _apply_jsonpath_add(
        self, data: Dict[str, Any], config: TransformationConfig
    ) -> Dict[str, Any]:
        """Apply JSON path add transformation.

        Args:
            data: Data to transform
            config: Transformation configuration

        Returns:
            Transformed data
        """
        if not config.path or config.value is None:
            return data

        try:
            # Work with a copy
            result = json.loads(json.dumps(data))

            # Parse the path
            path_parts = config.path.replace("$.", "").split(".")

            # Navigate to the parent and set the value
            current = result
            for i, part in enumerate(path_parts[:-1]):
                if part not in current:
                    # Create intermediate objects
                    current[part] = {}
                current = current[part]

            # Set the value
            last_part = path_parts[-1]
            current[last_part] = config.value

            logger.debug(f"Added value at path: {config.path}")
            return result

        except Exception as e:
            logger.error(f"Error applying jsonpath_add: {e}", exc_info=True)
            return data
