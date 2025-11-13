"""Data models for LLM Router Service."""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


# OpenAI Models
class OpenAIMessage(BaseModel):
    """OpenAI chat message."""

    role: str = Field(description="Message role: system, user, or assistant")
    content: str = Field(description="Message content")
    name: Optional[str] = Field(default=None, description="Optional name")


class OpenAIChatCompletionRequest(BaseModel):
    """OpenAI chat completion request."""

    model: str = Field(description="Model identifier")
    messages: List[OpenAIMessage] = Field(description="List of messages")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    n: Optional[int] = Field(default=None, ge=1)
    stream: Optional[bool] = Field(default=False, description="Enable streaming")
    stop: Optional[Union[str, List[str]]] = Field(default=None)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = Field(default=None)
    user: Optional[str] = Field(default=None)


class OpenAICompletionRequest(BaseModel):
    """OpenAI completion request."""

    model: str = Field(description="Model identifier")
    prompt: Union[str, List[str]] = Field(description="Prompt text")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    n: Optional[int] = Field(default=None, ge=1)
    stream: Optional[bool] = Field(default=False, description="Enable streaming")
    stop: Optional[Union[str, List[str]]] = Field(default=None)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = Field(default=None)
    user: Optional[str] = Field(default=None)


class OpenAIChoice(BaseModel):
    """OpenAI response choice."""

    index: int
    message: Optional[OpenAIMessage] = None
    text: Optional[str] = None
    finish_reason: Optional[str] = None


class OpenAIUsage(BaseModel):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenAIChatCompletionResponse(BaseModel):
    """OpenAI chat completion response."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[OpenAIChoice]
    usage: Optional[OpenAIUsage] = None


class OpenAICompletionResponse(BaseModel):
    """OpenAI completion response."""

    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: List[OpenAIChoice]
    usage: Optional[OpenAIUsage] = None


# Anthropic Models
class AnthropicMessage(BaseModel):
    """Anthropic message."""

    role: Literal["user", "assistant"] = Field(description="Message role")
    content: str = Field(description="Message content")


class AnthropicMessageRequest(BaseModel):
    """Anthropic message request."""

    model: str = Field(description="Model identifier")
    messages: List[AnthropicMessage] = Field(description="List of messages")
    max_tokens: int = Field(ge=1, description="Maximum tokens to generate")
    system: Optional[str] = Field(default=None, description="System prompt")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=None, ge=0)
    stop_sequences: Optional[List[str]] = Field(default=None)
    stream: Optional[bool] = Field(default=False, description="Enable streaming")
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class AnthropicContent(BaseModel):
    """Anthropic content block."""

    type: str = "text"
    text: str


class AnthropicMessageResponse(BaseModel):
    """Anthropic message response."""

    id: str
    type: str = "message"
    role: str = "assistant"
    content: List[AnthropicContent]
    model: str
    stop_reason: Optional[str] = None
    stop_sequence: Optional[str] = None
    usage: Dict[str, int]


# Error Models
class ErrorResponse(BaseModel):
    """Error response."""

    error: Dict[str, Any] = Field(description="Error details")

    @classmethod
    def from_exception(
        cls, error_type: str, message: str, status_code: int = 500
    ) -> "ErrorResponse":
        """Create error response from exception.

        Args:
            error_type: Type of error
            message: Error message
            status_code: HTTP status code

        Returns:
            ErrorResponse instance
        """
        return cls(
            error={
                "type": error_type,
                "message": message,
                "status_code": status_code,
            }
        )


# Streaming Models
class StreamChunk(BaseModel):
    """Generic streaming chunk."""

    data: str = Field(description="SSE data field")
    event: Optional[str] = Field(default=None, description="SSE event type")

    def to_sse(self) -> str:
        """Convert to SSE format.

        Returns:
            SSE formatted string
        """
        lines = []
        if self.event:
            lines.append(f"event: {self.event}")
        lines.append(f"data: {self.data}")
        lines.append("")
        return "\n".join(lines)
