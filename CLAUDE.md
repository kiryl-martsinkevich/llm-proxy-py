# LLM Router Service - Project Documentation

## Overview

This is a Python-based LLM router service that provides a unified interface for multiple LLM providers (OpenAI, Anthropic, Ollama) while offering advanced request/response manipulation capabilities.

## Architecture

### Core Components

1. **API Endpoints Layer**
   - OpenAI-compliant HTTP endpoint (streaming & non-streaming)
   - Anthropic-compliant HTTP endpoint
   - Built using FastAPI for async performance

2. **Router Layer**
   - Routes requests to configured backend providers
   - Supports OpenAI, Anthropic, and Ollama endpoints
   - Per-model API key configuration
   - HTTP/HTTPS support with optional SSL verification

3. **Middleware Layer**
   - **Header Manipulation**: Drop, add, or force HTTP headers
   - **Request/Response Logging**: Full logging with headers (configurable)
   - **Content Transformation**: Regex-based search/replace and JSON path operations
   - **Timeout & Retry**: Configurable retry logic for common errors

4. **Configuration Management**
   - YAML-based configuration
   - Model-to-endpoint mappings
   - Header rules
   - Transformation rules
   - Retry policies

## Key Features

### 1. Header Manipulation
- **Drop headers**: Remove specific headers from upstream requests
- **Add headers**: Add new headers to upstream requests
- **Force headers**: Override existing headers
- **Drop all mode**: Start with clean slate, only use configured headers

### 2. Request/Response Logging
- Optional full request logging (including headers)
- Optional full response logging (including headers)
- Configurable per endpoint or globally
- Sensitive data masking support

### 3. SSL Verification Control
- Disable SSL verification for specific endpoints
- Useful for development/testing with self-signed certificates

### 4. Timeout & Retry Configuration
- Configurable connection and read timeouts
- Retry logic for transient errors (429, 500, 502, 503, 504)
- Exponential backoff support
- Maximum retry attempts configuration

### 5. Content Transformation
- **Regex-based**: Search and replace in message content
- **JSON Path operations**:
  - Drop blocks at specified JSON paths
  - Add pre-configured blocks at specified JSON paths
- Applied before sending to upstream provider

## Technology Stack

- **Python 3.12+**
- **uv**: Fast Python package manager
- **FastAPI**: Modern web framework for building APIs
- **httpx**: Async HTTP client with streaming support
- **Pydantic**: Data validation and settings management
- **PyYAML**: Configuration file parsing
- **jsonpath-ng**: JSON path manipulation

## Configuration Example

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  log_requests: true
  log_responses: true

models:
  gpt-4:
    provider: openai
    endpoint: "https://api.openai.com/v1"
    api_key: "sk-..."
    timeout: 60
    retry_config:
      max_retries: 3
      retry_status_codes: [429, 500, 502, 503, 504]

  claude-3-opus:
    provider: anthropic
    endpoint: "https://api.anthropic.com"
    api_key: "sk-ant-..."
    ssl_verify: true

  llama-local:
    provider: ollama
    endpoint: "http://localhost:11434"
    ssl_verify: false

header_rules:
  drop_all: false
  drop_headers:
    - "x-forwarded-for"
    - "x-real-ip"
  add_headers:
    user-agent: "LLM-Router/1.0"
  force_headers:
    content-type: "application/json"

transformations:
  - name: "remove_system_prompts"
    type: "jsonpath_drop"
    path: "$.messages[?(@.role='system')]"

  - name: "sanitize_content"
    type: "regex_replace"
    pattern: "\\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}\\b"
    replacement: "[EMAIL]"
    flags: "IGNORECASE"
```

## API Endpoints

### OpenAI-Compatible

```
POST /v1/chat/completions
POST /v1/completions
POST /v1/embeddings
```

### Anthropic-Compatible

```
POST /v1/messages
```

## Request Flow

1. Client sends request to router endpoint
2. Router identifies target model from request
3. Header manipulation middleware processes headers
4. Content transformation middleware processes request body
5. Request is forwarded to configured upstream provider
6. Response is streamed back or returned as complete
7. Optional response logging and transformation

## Error Handling

- Automatic retry for transient errors
- Proper error propagation with status codes
- Detailed error logging
- Client-friendly error messages

## Security Considerations

- API key management per model
- Header sanitization
- Optional SSL verification (use carefully)
- Request/response logging includes sensitive data handling
