"""Configuration management for LLM Router Service."""

import os
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class RetryConfig(BaseModel):
    """Retry configuration for a model."""

    max_retries: int = Field(default=3, ge=0, description="Maximum number of retries")
    retry_status_codes: List[int] = Field(
        default=[429, 500, 502, 503, 504],
        description="HTTP status codes to retry on",
    )
    backoff_factor: float = Field(
        default=2.0, ge=1.0, description="Exponential backoff factor"
    )
    initial_delay: float = Field(
        default=1.0, ge=0.1, description="Initial delay in seconds"
    )
    max_delay: float = Field(
        default=60.0, ge=1.0, description="Maximum delay in seconds"
    )


class ModelConfig(BaseModel):
    """Configuration for a specific model."""

    provider: str = Field(description="Provider type: openai, anthropic, or ollama")
    endpoint: str = Field(description="Base URL for the provider API")
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    timeout: float = Field(default=60.0, ge=1.0, description="Request timeout in seconds")
    connect_timeout: float = Field(
        default=10.0, ge=1.0, description="Connection timeout in seconds"
    )
    ssl_verify: bool = Field(default=True, description="Verify SSL certificates")
    retry_config: Optional[RetryConfig] = Field(
        default=None, description="Retry configuration"
    )
    # Model name to send to the actual provider (if different from the key)
    actual_model_name: Optional[str] = Field(
        default=None,
        description="Actual model name to send to provider (overrides incoming model name)",
    )


class HeaderRuleConfig(BaseModel):
    """Header manipulation rules."""

    drop_all: bool = Field(
        default=False,
        description="Drop all incoming headers and only use configured ones",
    )
    drop_headers: List[str] = Field(
        default_factory=list,
        description="Headers to drop from requests (supports regex patterns)",
    )
    add_headers: Dict[str, str] = Field(
        default_factory=dict, description="Headers to add to requests"
    )
    force_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Headers to force (override if exists, add if not)",
    )


class TransformationConfig(BaseModel):
    """Content transformation configuration."""

    name: str = Field(description="Name of the transformation")
    type: str = Field(
        description="Transformation type: regex_replace, jsonpath_drop, or jsonpath_add"
    )
    enabled: bool = Field(default=True, description="Whether transformation is enabled")

    # For regex_replace
    pattern: Optional[str] = Field(default=None, description="Regex pattern to match")
    replacement: Optional[str] = Field(
        default=None, description="Replacement string for regex"
    )
    flags: Optional[str] = Field(
        default=None, description="Regex flags: IGNORECASE, MULTILINE, DOTALL"
    )

    # For jsonpath operations
    path: Optional[str] = Field(default=None, description="JSON path expression")
    value: Optional[Dict[str, Any]] = Field(
        default=None, description="Value to add for jsonpath_add"
    )


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8000, ge=1, le=65535, description="Port to bind to")
    log_requests: bool = Field(
        default=False, description="Log full requests including headers"
    )
    log_responses: bool = Field(
        default=False, description="Log full responses including headers"
    )
    mask_api_keys: bool = Field(
        default=True, description="Mask API keys in logs"
    )


class AppConfig(BaseModel):
    """Main application configuration."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    models: Dict[str, ModelConfig] = Field(
        default_factory=dict, description="Model configurations"
    )
    header_rules: HeaderRuleConfig = Field(default_factory=HeaderRuleConfig)
    transformations: List[TransformationConfig] = Field(
        default_factory=list, description="Content transformations"
    )
    default_retry_config: RetryConfig = Field(
        default_factory=RetryConfig, description="Default retry configuration"
    )

    @classmethod
    def from_yaml(cls, path: str) -> "AppConfig":
        """Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            AppConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        # Process environment variable overrides
        data = cls._process_env_overrides(data)

        return cls(**data)

    @staticmethod
    def _process_env_overrides(data: Dict[str, Any]) -> Dict[str, Any]:
        """Process environment variable overrides for sensitive values.

        Environment variables format:
        - LLM_ROUTER_MODEL_{MODEL_NAME}_API_KEY
        - LLM_ROUTER_SERVER_PORT
        """
        # Override model API keys from environment
        if "models" in data:
            for model_name, model_config in data["models"].items():
                env_key = f"LLM_ROUTER_MODEL_{model_name.upper().replace('-', '_')}_API_KEY"
                if env_value := os.getenv(env_key):
                    model_config["api_key"] = env_value

        # Override server settings
        if "server" not in data:
            data["server"] = {}

        if env_port := os.getenv("LLM_ROUTER_SERVER_PORT"):
            data["server"]["port"] = int(env_port)

        if env_host := os.getenv("LLM_ROUTER_SERVER_HOST"):
            data["server"]["host"] = env_host

        return data

    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model.

        Args:
            model_name: Name of the model

        Returns:
            ModelConfig if found, None otherwise
        """
        return self.models.get(model_name)

    def get_retry_config(self, model_name: str) -> RetryConfig:
        """Get retry configuration for a model.

        Args:
            model_name: Name of the model

        Returns:
            Model-specific retry config or default
        """
        if model_config := self.get_model_config(model_name):
            if model_config.retry_config:
                return model_config.retry_config
        return self.default_retry_config
