# Embedding Factory

Factory pattern implementation for managing different embedding providers.

## Structure

```
embedding_factory/
├── __init__.py
├── base.py                    # Base abstract class
├── embedding_factory.py       # Factory class
└── providers/
    ├── __init__.py
    ├── openai_provider.py     # OpenAI embeddings
    └── bedrock_provider.py    # AWS Bedrock embeddings
```

## Supported Providers

### OpenAI
- **Models**: 
  - `text-embedding-3-small` (1536 dimensions) - **Default**
  - `text-embedding-3-large` (3072 dimensions)
  - `text-embedding-ada-002` (1536 dimensions)
- **Configuration**: Requires `OPENAI_API_KEY`

### AWS Bedrock
- **Models**:
  - `amazon.titan-embed-text-v1` (1536 dimensions)
  - `amazon.titan-embed-text-v2` (1024 dimensions)
- **Configuration**: Requires AWS credentials (profile or keys)

## Usage

### Basic Usage

```python
from src.app.services.embedding_factory.embedding_factory import EmbeddingFactory

# Create OpenAI embedder (default)
embedder = EmbeddingFactory.create("openai", "text-embedding-3-small")

# Generate embeddings
text = "Hello, world!"
embeddings = embedder.embed(text)
print(f"Embedding dimensions: {len(embeddings)}")
```

### With Custom Configuration

```python
# OpenAI with custom API key
embedder = EmbeddingFactory.create(
    "openai",
    "text-embedding-3-large",
    api_key="sk-..."
)

# AWS Bedrock with custom region
embedder = EmbeddingFactory.create(
    "bedrock",
    "amazon.titan-embed-text-v1",
    aws_region="us-west-2"
)
```

### Batch Embeddings (OpenAI only)

```python
embedder = EmbeddingFactory.create("openai")

texts = ["First text", "Second text", "Third text"]
embeddings_list = embedder.embed_batch(texts)
```

### Get Model Dimensions

```python
# Get dimensions for a specific model
dims = EmbeddingFactory.get_model_dimensions("openai", "text-embedding-3-small")
print(f"Dimensions: {dims}")  # 1536

# Or from the embedder instance
embedder = EmbeddingFactory.create("openai", "text-embedding-3-small")
dims = embedder.get_dimensions()
```

## Configuration via Settings

The embedding factory uses settings from `config.py`:

```python
# config.py
EMBEDDING_PROVIDER: str = "openai"  # or "bedrock"
EMBEDDING_MODEL: str = "text-embedding-3-small"
VECTOR_DIMENSIONS: int = 1536
```

These can be overridden via environment variables:

```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=sk-...
```

## Integration with Vector Stores

### Elasticsearch Example

```python
from src.app.vectorstores.elastic_search import ElasticSearchService

# Elasticsearch will automatically use the configured embedding provider
es_service = ElasticSearchService(
    hosts=["https://localhost:9200"],
    embedding_provider="openai",  # Optional, uses config default
    embedding_model="text-embedding-3-small"  # Optional, uses config default
)

# Use the embed method
text = "Sample text to embed"
vector = es_service.embed(text)

# Create vector index with appropriate dimensions
es_service.create_vector_index(
    index_name="my_index",
    text_fields=["content", "title"],
    vector_dims=1536  # Or use embedder.get_dimensions()
)
```

## Adding New Providers

To add a new embedding provider:

1. Create a new provider file in `providers/`
2. Implement the `BaseEmbeddingProvider` interface
3. Register in `EmbeddingFactory.PROVIDERS`

Example:

```python
# providers/custom_provider.py
from ..base import BaseEmbeddingProvider
from typing import List

class CustomEmbeddingProvider(BaseEmbeddingProvider):
    def create(self, model: str, **kwargs):
        # Initialize your provider
        self.client = CustomClient(model=model, **kwargs)
        self.model = model
        return self
    
    def embed(self, text: str) -> List[float]:
        # Generate embeddings
        return self.client.embed(text)
    
    def get_dimensions(self) -> int:
        # Return embedding dimensions
        return 768  # Example
```

## Error Handling

All providers handle errors gracefully:

```python
embedder = EmbeddingFactory.create("openai")

# If embedding fails, returns empty list
embeddings = embedder.embed("Some text")
if not embeddings:
    print("Embedding generation failed")
```

## Model Comparison

| Provider | Model | Dimensions | Cost/1M tokens | Speed |
|----------|-------|------------|----------------|-------|
| OpenAI | text-embedding-3-small | 1536 | $0.02 | Fast |
| OpenAI | text-embedding-3-large | 3072 | $0.13 | Medium |
| OpenAI | text-embedding-ada-002 | 1536 | $0.10 | Fast |
| Bedrock | titan-embed-text-v1 | 1536 | $0.10 | Medium |

## Best Practices

1. **Use `text-embedding-3-small`** for most applications (good balance of performance and cost)
2. **Use batch embedding** when processing multiple texts (OpenAI only)
3. **Cache embeddings** for frequently accessed texts
4. **Match dimensions** when creating vector indexes
5. **Handle errors** gracefully with empty list checks

## License

MIT
