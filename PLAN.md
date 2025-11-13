# LLM Router Service - Implementation Plan

## Phase 1: Project Setup

### 1.1 Initialize uv Project
- [ ] Initialize uv project structure
- [ ] Create pyproject.toml with dependencies
- [ ] Set up directory structure
- [ ] Configure Python 3.12+

### 1.2 Dependencies
```toml
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "httpx>=0.26.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "pyyaml>=6.0",
    "jsonpath-ng>=1.6.0",
    "python-multipart>=0.0.6",
]
```

### 1.3 Directory Structure
```
llm-proxy-py/
├── pyproject.toml
├── README.md
├── CLAUDE.md
├── PLAN.md
├── config.example.yaml
├── src/
│   └── llm_router/
│       ├── __init__.py
│       ├── main.py              # FastAPI app entry point
│       ├── config.py            # Configuration management
│       ├── models.py            # Pydantic models
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── headers.py       # Header manipulation
│       │   ├── logging.py       # Request/response logging
│       │   └── transform.py     # Content transformation
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── openai.py        # OpenAI-compatible endpoints
│       │   └── anthropic.py     # Anthropic-compatible endpoints
│       ├── clients/
│       │   ├── __init__.py
│       │   ├── base.py          # Base client with retry logic
│       │   ├── openai.py        # OpenAI client
│       │   ├── anthropic.py     # Anthropic client
│       │   └── ollama.py        # Ollama client
│       └── utils/
│           ├── __init__.py
│           ├── retry.py         # Retry logic
│           └── streaming.py     # Streaming utilities
└── tests/
    └── ...
```

## Phase 2: Core Configuration

### 2.1 Configuration Models (config.py)
- [ ] ServerConfig: Host, port, logging settings
- [ ] ModelConfig: Provider, endpoint, API key, timeouts, SSL settings
- [ ] HeaderRuleConfig: Drop/add/force rules
- [ ] TransformationConfig: Regex and JSON path rules
- [ ] RetryConfig: Max retries, backoff, status codes
- [ ] AppConfig: Main configuration container

### 2.2 Configuration Loading
- [ ] YAML file loader
- [ ] Environment variable overrides
- [ ] Configuration validation
- [ ] Default values

## Phase 3: Middleware Implementation

### 3.1 Header Manipulation Middleware (middleware/headers.py)
- [ ] HeaderManipulator class
- [ ] Drop specific headers
- [ ] Add new headers
- [ ] Force/override headers
- [ ] Drop all mode (whitelist approach)
- [ ] Apply to outgoing requests

### 3.2 Logging Middleware (middleware/logging.py)
- [ ] RequestLogger class
- [ ] Log full request (optional)
- [ ] Log headers (optional)
- [ ] Log response (optional)
- [ ] Mask sensitive data (API keys, tokens)
- [ ] Structured logging format

### 3.3 Content Transformation Middleware (middleware/transform.py)
- [ ] ContentTransformer class
- [ ] Regex-based search/replace
  - [ ] Compile patterns with flags
  - [ ] Apply to message content
- [ ] JSON path operations
  - [ ] Drop blocks at JSON path
  - [ ] Add blocks at JSON path
  - [ ] Handle array and object paths
- [ ] Apply transformations in order

## Phase 4: HTTP Client Layer

### 4.1 Base Client (clients/base.py)
- [ ] BaseClient abstract class
- [ ] HTTPX async client configuration
- [ ] SSL verification toggle
- [ ] Timeout configuration
- [ ] Retry logic integration
- [ ] Header manipulation integration
- [ ] Error handling

### 4.2 Retry Logic (utils/retry.py)
- [ ] RetryHandler class
- [ ] Exponential backoff calculation
- [ ] Configurable retry conditions
- [ ] Status code-based retry
- [ ] Exception-based retry
- [ ] Max attempts enforcement

### 4.3 Provider Clients
- [ ] OpenAIClient (clients/openai.py)
  - [ ] Non-streaming requests
  - [ ] Streaming requests (SSE)
  - [ ] Request formatting
- [ ] AnthropicClient (clients/anthropic.py)
  - [ ] Non-streaming requests
  - [ ] Streaming requests (SSE)
  - [ ] Request formatting
- [ ] OllamaClient (clients/ollama.py)
  - [ ] Non-streaming requests
  - [ ] Streaming requests
  - [ ] Request formatting

## Phase 5: API Endpoints

### 5.1 OpenAI-Compatible Router (routers/openai.py)
- [ ] POST /v1/chat/completions
  - [ ] Non-streaming mode
  - [ ] Streaming mode (SSE)
  - [ ] Model routing
  - [ ] Error handling
- [ ] POST /v1/completions
  - [ ] Non-streaming mode
  - [ ] Streaming mode
- [ ] Request validation
- [ ] Response formatting

### 5.2 Anthropic-Compatible Router (routers/anthropic.py)
- [ ] POST /v1/messages
  - [ ] Non-streaming mode
  - [ ] Streaming mode (SSE)
  - [ ] Model routing
  - [ ] Error handling
- [ ] Request validation
- [ ] Response formatting

### 5.3 Streaming Utilities (utils/streaming.py)
- [ ] SSE formatter for OpenAI
- [ ] SSE formatter for Anthropic
- [ ] Stream proxy/relay
- [ ] Error handling in streams
- [ ] Stream termination

## Phase 6: Main Application

### 6.1 FastAPI Application (main.py)
- [ ] Create FastAPI app
- [ ] Register routers
- [ ] Add middleware
- [ ] Global exception handler
- [ ] Startup/shutdown events
- [ ] Health check endpoint
- [ ] Configuration loading

### 6.2 Application Lifecycle
- [ ] Load configuration on startup
- [ ] Initialize HTTP clients
- [ ] Validate model configurations
- [ ] Graceful shutdown
- [ ] Connection pool cleanup

## Phase 7: Data Models

### 7.1 Request Models (models.py)
- [ ] OpenAIChatCompletionRequest
- [ ] OpenAICompletionRequest
- [ ] AnthropicMessageRequest
- [ ] Message models
- [ ] Streaming parameters

### 7.2 Response Models
- [ ] OpenAIChatCompletionResponse
- [ ] OpenAICompletionResponse
- [ ] AnthropicMessageResponse
- [ ] Error response models
- [ ] Streaming chunk models

## Phase 8: Configuration & Documentation

### 8.1 Example Configuration
- [ ] Create config.example.yaml
- [ ] Document all configuration options
- [ ] Provide multiple model examples
- [ ] Include transformation examples
- [ ] Add header manipulation examples

### 8.2 Documentation
- [ ] README.md with quick start
- [ ] Installation instructions
- [ ] Configuration guide
- [ ] API usage examples
- [ ] Troubleshooting section

## Phase 9: Testing & Validation

### 9.1 Manual Testing
- [ ] Test OpenAI endpoint (non-streaming)
- [ ] Test OpenAI endpoint (streaming)
- [ ] Test Anthropic endpoint (non-streaming)
- [ ] Test Anthropic endpoint (streaming)
- [ ] Test header manipulation
- [ ] Test content transformation
- [ ] Test retry logic
- [ ] Test SSL verification toggle
- [ ] Test logging

### 9.2 Error Scenarios
- [ ] Invalid model name
- [ ] Upstream timeout
- [ ] Upstream error (500, 502, etc.)
- [ ] Rate limiting (429)
- [ ] Invalid API key
- [ ] Malformed request

## Implementation Order

1. **Phase 1**: Project setup and dependencies
2. **Phase 2**: Configuration management
3. **Phase 7**: Data models (needed for other phases)
4. **Phase 3**: Middleware implementation
5. **Phase 4**: HTTP client layer
6. **Phase 5**: API endpoints
7. **Phase 6**: Main application
8. **Phase 8**: Configuration and documentation
9. **Phase 9**: Testing and validation

## Key Implementation Notes

### Streaming Considerations
- Use FastAPI's `StreamingResponse` for SSE
- Handle backpressure properly
- Ensure proper error handling in streams
- Close connections gracefully

### Security
- Never log full API keys (mask them)
- Validate all inputs
- Sanitize error messages
- Use HTTPS by default

### Performance
- Use connection pooling (httpx)
- Async/await throughout
- Efficient JSON parsing
- Minimize request/response copying

### Error Handling
- Wrap all external calls in try/except
- Propagate appropriate HTTP status codes
- Log errors with context
- Provide helpful error messages

### Configuration Flexibility
- Support environment variable overrides
- Allow per-model configuration
- Support global defaults
- Validate configuration at startup

## Success Criteria

- [ ] OpenAI endpoints work with streaming and non-streaming
- [ ] Anthropic endpoints work with streaming and non-streaming
- [ ] Headers can be manipulated per configuration
- [ ] Request/response logging works
- [ ] SSL verification can be disabled
- [ ] Timeouts are respected
- [ ] Retries work for configured error codes
- [ ] Content transformations apply correctly
- [ ] Multiple models can be configured
- [ ] Clear documentation exists
