# LLM Router Service

A Python-based LLM router service that provides a unified interface for multiple LLM providers (OpenAI, Anthropic, Ollama) with advanced request/response manipulation capabilities.

## Features

- **Multiple Provider Support**: OpenAI, Anthropic, and Ollama endpoints
- **Model Aliasing**: Route requests for one model to a different provider/model
- **OpenAI-Compatible API**: Exposes `/v1/chat/completions` and `/v1/completions` endpoints
- **Anthropic-Compatible API**: Exposes `/v1/messages` endpoint
- **Streaming Support**: Full streaming support for all providers
- **Header Manipulation**: Drop (with regex support), add, or force HTTP headers
- **Request/Response Logging**: Optional full logging with sensitive data masking
- **Content Transformation**: Regex-based and JSON path operations
- **Retry Logic**: Configurable retry with exponential backoff
- **SSL Verification Control**: Disable SSL verification for development/testing
- **Per-Model Configuration**: Different settings for each model

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

```bash
# Clone the repository
git clone <repository-url>
cd llm-proxy-py

# Install dependencies using uv
uv sync

# Or install uv first if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Quick Start

1. **Create Configuration**

```bash
cp config.example.yaml config.yaml
```

2. **Edit `config.yaml`** and add your API keys:

```yaml
models:
  gpt-4:
    provider: openai
    endpoint: "https://api.openai.com/v1"
    api_key: "sk-your-key-here"

  claude-3-opus:
    provider: anthropic
    endpoint: "https://api.anthropic.com"
    api_key: "sk-ant-your-key-here"
```

3. **Run the Server**

```bash
# Using uv
uv run llm-router

# Or with custom config
uv run llm-router --config config.yaml

# Development mode with auto-reload
uv run llm-router --reload

# Custom host and port
uv run llm-router --host 127.0.0.1 --port 9000
```

4. **Test the API**

```bash
# OpenAI-compatible endpoint
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Anthropic endpoint
curl http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-opus",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'

# Health check
curl http://localhost:8000/health
```

## Configuration

### Server Settings

```yaml
server:
  host: "0.0.0.0"          # Bind address
  port: 8000                # Bind port
  log_requests: true        # Log full requests
  log_responses: true       # Log full responses
  mask_api_keys: true       # Mask API keys in logs
```

### Model Configuration

```yaml
models:
  model-name:
    provider: openai|anthropic|ollama
    endpoint: "https://api.provider.com"
    api_key: "your-key"
    timeout: 60.0           # Request timeout (seconds)
    connect_timeout: 10.0   # Connection timeout (seconds)
    ssl_verify: true        # Verify SSL certificates
    actual_model_name: "real-model"  # Optional: override model name sent to provider
    retry_config:           # Optional retry configuration
      max_retries: 3
      retry_status_codes: [429, 500, 502, 503, 504]
      backoff_factor: 2.0
      initial_delay: 1.0
      max_delay: 60.0
```

#### Model Aliasing

You can route requests for one model name to a different provider/model using `actual_model_name`:

```yaml
models:
  # Client requests "gpt-4" but actually uses local Ollama
  gpt-4:
    provider: ollama
    endpoint: "http://localhost:11434"
    actual_model_name: "llama3"  # Send "llama3" to Ollama
    ssl_verify: false

  # Client requests "gpt-4-cheap" but uses gpt-3.5-turbo
  gpt-4-cheap:
    provider: openai
    endpoint: "https://api.openai.com/v1"
    api_key: "sk-your-key"
    actual_model_name: "gpt-3.5-turbo"
```

### Header Manipulation

Headers can be dropped, added, or forced. Drop rules support both exact matches and regex patterns:

```yaml
header_rules:
  drop_all: false           # Drop all headers, use only configured
  drop_headers:             # Headers to drop (supports regex)
    - "x-forwarded-for"     # Exact match
    - "^x-.*"               # Regex: all headers starting with "x-"
    - ".*-token$"           # Regex: all headers ending with "-token"
  add_headers:              # Headers to add if not exist
    user-agent: "LLM-Router/1.0"
  force_headers:            # Headers to force (override)
    content-type: "application/json"
```

### Content Transformations

```yaml
transformations:
  # Regex replacement
  - name: "sanitize_emails"
    type: "regex_replace"
    enabled: true
    pattern: '\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b'
    replacement: "[EMAIL]"
    flags: "IGNORECASE"

  # Drop JSON path
  - name: "remove_system_prompts"
    type: "jsonpath_drop"
    enabled: true
    path: "$.messages[?(@.role='system')]"

  # Add JSON path
  - name: "add_metadata"
    type: "jsonpath_add"
    enabled: true
    path: "$.metadata"
    value:
      source: "llm-router"
```

### Environment Variables

Override configuration with environment variables:

```bash
# Model API keys
export LLM_ROUTER_MODEL_GPT_4_API_KEY="sk-new-key"
export LLM_ROUTER_MODEL_CLAUDE_3_OPUS_API_KEY="sk-ant-new-key"

# Server settings
export LLM_ROUTER_SERVER_PORT=9000
export LLM_ROUTER_SERVER_HOST="127.0.0.1"
```

## API Endpoints

### OpenAI-Compatible

#### POST /v1/chat/completions

Chat completions with streaming support.

```json
{
  "model": "gpt-4",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 100
}
```

#### POST /v1/completions

Text completions with streaming support.

```json
{
  "model": "gpt-4",
  "prompt": "Once upon a time",
  "stream": false,
  "max_tokens": 100
}
```

### Anthropic-Compatible

#### POST /v1/messages

Create messages with streaming support.

```json
{
  "model": "claude-3-opus",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "max_tokens": 100,
  "stream": false
}
```

### Utility Endpoints

#### GET /health

Health check endpoint.

```json
{
  "status": "healthy",
  "service": "llm-router",
  "version": "0.1.0",
  "models": ["gpt-4", "claude-3-opus"]
}
```

## Streaming

All endpoints support streaming responses. Enable streaming by setting `"stream": true` in the request body.

```bash
# OpenAI streaming
curl -N http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Count to 5"}],
    "stream": true
  }'

# Anthropic streaming
curl -N http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-opus",
    "messages": [{"role": "user", "content": "Count to 5"}],
    "max_tokens": 100,
    "stream": true
  }'
```

## Use Cases

### 1. Multi-Provider Routing

Route requests to different providers based on model name:

```yaml
models:
  gpt-4:
    provider: openai
    endpoint: "https://api.openai.com/v1"
    api_key: "sk-openai-key"

  claude-3-opus:
    provider: anthropic
    endpoint: "https://api.anthropic.com"
    api_key: "sk-ant-key"

  llama3-local:
    provider: ollama
    endpoint: "http://localhost:11434"
    ssl_verify: false
```

### 2. Content Filtering

Remove sensitive information before sending to LLM:

```yaml
transformations:
  - name: "remove_emails"
    type: "regex_replace"
    enabled: true
    pattern: '\b[\w\.-]+@[\w\.-]+\.\w+\b'
    replacement: "[EMAIL]"

  - name: "remove_phone_numbers"
    type: "regex_replace"
    enabled: true
    pattern: '\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    replacement: "[PHONE]"
```

### 3. Custom Headers

Add custom headers for authentication or tracking:

```yaml
header_rules:
  force_headers:
    user-agent: "MyApp/1.0"
    x-request-id: "unique-id"
    x-api-version: "2024-01"
```

### 4. Development with Self-Signed Certs

Disable SSL verification for local development:

```yaml
models:
  local-model:
    provider: openai
    endpoint: "https://localhost:8443/v1"
    ssl_verify: false  # Only for development!
```

## Logging

The service provides comprehensive logging with sensitive data masking:

```yaml
server:
  log_requests: true     # Log all requests
  log_responses: true    # Log all responses
  mask_api_keys: true    # Mask API keys (recommended)
```

Logs include:
- Request method, URL, headers, and body
- Response status, headers, and body
- Retry attempts and delays
- Errors with stack traces

API keys are automatically masked in logs:
- `sk-1234567890abcdef...` → `sk-12345...cdef`

## Error Handling

The service handles errors gracefully:

- **404**: Model not found in configuration
- **500**: Internal server error
- **Upstream errors**: Propagated from provider with retries

Retry is automatic for:
- Status codes: 429, 500, 502, 503, 504
- Network errors: Connection errors, timeouts
- Exponential backoff with configurable delays

## Development

```bash
# Install development dependencies
uv sync

# Run with auto-reload
uv run llm-router --reload

# Run tests (when available)
uv run pytest

# Format code
uv run ruff format

# Lint code
uv run ruff check
```

## Project Structure

```
llm-proxy-py/
├── src/llm_router/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── middleware/
│   │   ├── headers.py       # Header manipulation
│   │   ├── logging.py       # Request/response logging
│   │   └── transform.py     # Content transformation
│   ├── clients/
│   │   ├── base.py          # Base HTTP client
│   │   ├── openai.py        # OpenAI client
│   │   ├── anthropic.py     # Anthropic client
│   │   └── ollama.py        # Ollama client
│   ├── routers/
│   │   ├── openai.py        # OpenAI endpoints
│   │   └── anthropic.py     # Anthropic endpoints
│   └── utils/
│       ├── retry.py         # Retry logic
│       └── streaming.py     # Streaming utilities
├── config.example.yaml      # Example configuration
├── pyproject.toml          # Project metadata
├── README.md               # This file
├── CLAUDE.md               # Architecture documentation
└── PLAN.md                 # Implementation plan
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.

## Documentation

- [CLAUDE.md](CLAUDE.md) - Architecture and design documentation
- [PLAN.md](PLAN.md) - Implementation plan and roadmap
- [config.example.yaml](config.example.yaml) - Configuration reference
