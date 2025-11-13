# Using Claude Code with Local Ollama Models

This guide shows you how to use Claude Code with local Ollama models instead of cloud providers. This is useful for:

- Privacy: Keep your code on your local machine
- Cost savings: No API costs
- Offline development: Work without internet
- Experimentation: Try different open-source models

## Prerequisites

1. **Install Ollama**
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh

   # Or download from https://ollama.ai
   ```

2. **Pull a model**
   ```bash
   # Pull the gpt-oss:20b model (or any other model you prefer)
   ollama pull gpt-oss:20b

   # Alternative models:
   # ollama pull llama3:70b     # Larger, more capable
   # ollama pull llama3:8b      # Faster, smaller
   # ollama pull codellama:34b  # Optimized for code
   # ollama pull mistral:latest
   # ollama pull mixtral:8x7b
   ```

3. **Verify Ollama is running**
   ```bash
   curl http://localhost:11434/api/tags
   ```

## Setup

### 1. Start the LLM Router

```bash
# From the llm-proxy-py directory
uv run llm-router --config config.claude-code-ollama.yaml
```

You should see output like:
```
2025-11-13 23:30:00 - INFO - Starting LLM Router Service...
2025-11-13 23:30:00 - INFO - Loaded 11 model(s)
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Configure Claude Code

Claude Code needs to be configured to use your local router instead of the Anthropic API.

**Option A: Environment Variables**

```bash
# Set the API endpoint
export ANTHROPIC_API_URL="http://localhost:8000"

# Use any API key (it's not validated for local Ollama)
export ANTHROPIC_API_KEY="sk-local-ollama"

# Start Claude Code
claude-code
```

**Option B: Configuration File**

Edit Claude Code's configuration file and set:
```json
{
  "api_url": "http://localhost:8000",
  "api_key": "sk-local-ollama"
}
```

### 3. Test the Setup

Start a conversation in Claude Code. Your requests should now be routed to your local Ollama instance!

## How It Works

1. Claude Code sends requests for models like `claude-3-5-sonnet-20241022`
2. The LLM Router intercepts these requests
3. The router translates the model name to `gpt-oss:20b` (or whatever you configured)
4. The request is forwarded to your local Ollama instance
5. Ollama processes it with the local model
6. The response is returned to Claude Code

## Monitoring

With `log_requests: true` in the config, you can watch the router logs to see:
- Which model Claude Code is requesting
- What model it's being translated to
- Request/response details (useful for debugging)

```bash
# Watch the logs
tail -f /tmp/llm-router.log
```

## Customizing the Model

### Using a Different Model

Edit `config.claude-code-ollama.yaml` and change all `actual_model_name` fields:

```yaml
models:
  claude-3-5-sonnet-20241022:
    provider: ollama
    endpoint: "http://localhost:11434"
    actual_model_name: "llama3:70b"  # Changed from gpt-oss:20b
```

### Different Models for Different Claude Versions

You can map different Claude models to different Ollama models:

```yaml
models:
  # Use large model for Opus
  claude-3-opus-20240229:
    provider: ollama
    endpoint: "http://localhost:11434"
    actual_model_name: "llama3:70b"

  # Use medium model for Sonnet
  claude-3-sonnet-20240229:
    provider: ollama
    endpoint: "http://localhost:11434"
    actual_model_name: "llama3:13b"

  # Use fast model for Haiku
  claude-3-haiku-20240307:
    provider: ollama
    endpoint: "http://localhost:11434"
    actual_model_name: "llama3:8b"
```

## Troubleshooting

### Router won't start

**Error: `Address already in use`**
```bash
# Kill existing process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Ollama not responding

**Error: `Connection refused to localhost:11434`**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start Ollama
ollama serve
```

### Model not found

**Error: `model 'gpt-oss:20b' not found`**
```bash
# Pull the model
ollama pull gpt-oss:20b

# List available models
ollama list
```

### Slow responses

- Try a smaller model (`llama3:8b` instead of `llama3:70b`)
- Increase timeout in config:
  ```yaml
  timeout: 300.0  # 5 minutes
  ```
- Check your system resources (CPU/RAM/VRAM usage)

### Incorrect responses

- The model quality varies greatly between models
- Try different models to find one that works well for your use case
- Models optimized for code (like `codellama`) may work better for Claude Code
- Larger models generally produce better results but are slower

## Performance Tips

1. **Use GPU acceleration**: Ollama will use your GPU if available
2. **Start with smaller models**: Test with `llama3:8b` first, then try larger ones
3. **Adjust context window**: Some models support larger contexts
4. **Keep Ollama running**: Starting Ollama takes time, keep it running in background

## Recommended Models for Claude Code

Based on use case:

| Use Case | Recommended Model | Notes |
|----------|-------------------|-------|
| General coding | `codellama:34b` | Best balance of speed/quality for code |
| Fast iteration | `llama3:8b` | Quick responses, decent quality |
| Best quality | `llama3:70b` | Slow but high quality, needs 40GB+ RAM |
| Balanced | `gpt-oss:20b` | Good middle ground |
| Reasoning | `mixtral:8x7b` | Good at complex reasoning tasks |

## Switching Back to Cloud

To switch back to using Anthropic's API:

1. Stop the router (Ctrl+C)
2. Remove the environment variables or config overrides
3. Use your real Anthropic API key

```bash
unset ANTHROPIC_API_URL
export ANTHROPIC_API_KEY="sk-ant-your-real-key"
```

## Security Notes

- This setup is for local development only
- Don't expose the router to the internet without authentication
- The router doesn't validate API keys for local Ollama
- All data stays on your local machine

## Further Reading

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Ollama Model Library](https://ollama.ai/library)
- [LLM Router Configuration Guide](config.example.yaml)
