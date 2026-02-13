# LLM Factory

A well-structured, provider-based LLM factory for creating model clients using the new autogen ChatCompletionClient interface.

## Architecture

```
llm_factory/
├── __init__.py                 # Main exports
├── base.py                     # Abstract base provider class
├── llm_factory.py              # Factory class
└── providers/                  # Provider implementations
    ├── __init__.py
    ├── openai_provider.py      # ✅ Implemented
    ├── gemini_provider.py      # ⏳ TODO
    ├── grok_provider.py        # ⏳ TODO
    └── llama_provider.py       # ⏳ TODO
```

## Features

- **Clean Provider Pattern**: Each LLM provider is isolated in its own class
- **New Autogen Pattern**: Uses ChatCompletionClient interface (autogen 0.4+)
- **Easy to Extend**: Add new providers by inheriting from `BaseProvider`
- **Type-Safe**: Proper type hints throughout
- **Simple API**: Single factory method to create any model client

## Usage

### Basic Usage with OpenAI (Implemented)

```python
from src.app.services.llm_factory import LLMFactory
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console

# Create model client
model_client = LLMFactory.create("openai", "gpt-4o", temperature=0.7)

# Define a simple tool
async def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    return f"The weather in {city} is 73 degrees and Sunny."

# Create an AssistantAgent
agent = AssistantAgent(
    name="weather_agent",
    model_client=model_client,
    tools=[get_weather],
    system_message="You are a helpful assistant.",
    reflect_on_tool_use=True,
    model_client_stream=True,
)

# Run the agent
async def main():
    await Console(agent.run_stream(task="What is the weather in New York?"))
    await model_client.close()

# In a script: asyncio.run(main())
# In a notebook: await main()
```

### Creating Model Clients

```python
from src.app.services.llm_factory import LLMFactory

# OpenAI - Implemented ✅
model_client = LLMFactory.create("openai", "gpt-4o", temperature=0.7)

# With custom API key
model_client = LLMFactory.create(
    "openai",
    "gpt-4",
    api_key="sk-...",
    temperature=0.2
)

# Other providers - TODO ⏳
# model_client = LLMFactory.create("gemini", "gemini-pro")
# model_client = LLMFactory.create("grok", "grok-beta")
# model_client = LLMFactory.create("llama", "llama3")
```

### Check Implementation Status

```python
# Get all supported providers (including unimplemented)
all_providers = LLMFactory.get_supported_providers()
print(all_providers)  # ['openai', 'gemini', 'grok', 'llama']

# Get only implemented providers
implemented = LLMFactory.get_implemented_providers()
print(implemented)  # ['openai']
```

## Supported Providers

### ✅ OpenAI (Implemented)
- **Models**: `gpt-4o`, `gpt-4`, `gpt-3.5-turbo`, etc.
- **Environment Variable**: `OPENAI_API_KEY`
- **Implementation**: Uses `autogen_ext.models.openai.OpenAIChatCompletionClient`

### ⏳ Gemini (TODO)
- **Models**: `gemini-pro`, `gemini-1.5-pro`, etc.
- **Environment Variable**: `GEMINI_API_KEY`
- **Status**: Waiting for autogen_ext.models.gemini documentation

### ⏳ Grok (TODO)
- **Models**: `grok-beta`, etc.
- **Environment Variable**: `GROK_API_KEY`
- **Status**: May work with OpenAIChatCompletionClient using custom base_url
- **Note**: Grok uses OpenAI-compatible API

### ⏳ Llama (TODO)
- **Models**: `llama2`, `llama3`, `llama3.1`, etc.
- **Local**: Runs on `http://localhost:11434/v1`
- **Status**: May work with OpenAIChatCompletionClient using custom base_url
- **Note**: Ollama provides OpenAI-compatible API

## Adding a New Provider

1. Create a new provider file in `providers/`:

```python
# providers/my_provider.py
import os
from typing import Any, Optional
from autogen_ext.models.custom import CustomChatCompletionClient
from ..base import BaseProvider


class MyProvider(BaseProvider):
    def create(
        self,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.2,
        **kwargs: Any
    ) -> CustomChatCompletionClient:
        return CustomChatCompletionClient(
            model=model,
            api_key=api_key or os.getenv("MY_API_KEY"),
            temperature=temperature,
            **kwargs
        )
```

2. Add it to `llm_factory.py`:

```python
from .providers.my_provider import MyProvider

class LLMFactory:
    PROVIDERS = {
        # ... existing providers
        "myprovider": MyProvider(),
    }
```

3. Update `get_implemented_providers()`:

```python
@classmethod
def get_implemented_providers(cls) -> list[str]:
    return ["openai", "myprovider"]
```

## Environment Setup

Create a `.env` file with your API keys:

```bash
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
GROK_API_KEY=your_grok_key_here
```

For Llama (Ollama), make sure Ollama is running locally:

```bash
ollama serve
```

## Installation

Make sure you have the required autogen packages:

```bash
uv pip install -U "autogen-agentchat" "autogen-ext[openai,azure]"
```

## Error Handling

The factory raises `ValueError` if an unsupported provider is requested:

```python
try:
    model_client = LLMFactory.create("invalid_provider", "some-model")
except ValueError as e:
    print(e)  # "Unsupported provider: invalid_provider..."
```

The factory raises `NotImplementedError` if a provider is not yet implemented:

```python
try:
    model_client = LLMFactory.create("gemini", "gemini-pro")
except NotImplementedError as e:
    print(e)  # "Gemini provider not yet implemented..."
```

## Migration from Old Pattern

### Old Pattern (autogen 0.2.x)
```python
from autogen import LLMConfig

llm_config = LLMConfig(
    config_list=[{"model": "gpt-4", "api_key": "..."}],
    temperature=0.7
)
```

### New Pattern (autogen 0.4+)
```python
from src.app.services.llm_factory import LLMFactory

model_client = LLMFactory.create("openai", "gpt-4o", temperature=0.7)
```

## Contributing

When implementing a new provider:
1. Test with actual API calls
2. Update `get_implemented_providers()`
3. Remove TODO comments
4. Update this README
5. Add usage examples
