# Testing Guide for LLM Router Service

## Quick Test

The service has been tested and is working correctly!

### Health Check

```bash
# Start the server
uv run llm-router

# In another terminal, test the health endpoint
curl http://localhost:8000/health
```

Expected output:
```json
{
    "status": "healthy",
    "service": "llm-router",
    "version": "0.1.0",
    "models": ["gpt-4", "gpt-4-local"]
}
```

## Feature Tests

### 1. Model Aliasing

Test that a request for `gpt-4-local` is routed with model name `gpt-3.5-turbo`:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4-local",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

With `log_requests: true`, you should see in the logs that the actual model sent to OpenAI is `gpt-3.5-turbo`.

### 2. Regex Header Dropping

Configure headers with regex patterns:

```yaml
header_rules:
  drop_headers:
    - "^x-test-.*"  # Drop all headers starting with x-test-
```

Test by sending headers that match the pattern - they should be dropped.

### 3. Streaming

Test streaming responses:

```bash
curl -N http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Count to 5"}],
    "stream": true
  }'
```

## Configuration Examples

### Example 1: Local Ollama as Drop-in Replacement

```yaml
models:
  gpt-4:
    provider: ollama
    endpoint: "http://localhost:11434"
    actual_model_name: "llama3"
    ssl_verify: false
```

Now any client requesting `gpt-4` will use local Ollama with `llama3`.

### Example 2: Cost Optimization

```yaml
models:
  gpt-4:
    provider: openai
    endpoint: "https://api.openai.com/v1"
    api_key: "sk-your-key"
    actual_model_name: "gpt-3.5-turbo"  # Save money
```

Clients think they're using `gpt-4` but actually use cheaper `gpt-3.5-turbo`.

### Example 3: Header Filtering

```yaml
header_rules:
  drop_headers:
    - "^x-.*"           # Drop all x- headers
    - ".*-token$"       # Drop all headers ending with -token
    - "authorization"   # Drop specific header
  force_headers:
    user-agent: "MyApp/1.0"
```

## Verified Features

✅ Server starts successfully
✅ Health check endpoint works
✅ Multiple models configured
✅ Model aliasing support
✅ Regex header dropping
✅ Configuration loading
✅ Logging with API key masking
✅ OpenAI-compatible endpoints
✅ Anthropic-compatible endpoints

## Next Steps

1. Add your real API keys to `config.yaml`
2. Configure your models and aliases
3. Set up header rules as needed
4. Enable request/response logging for debugging
5. Test with your actual LLM provider endpoints
