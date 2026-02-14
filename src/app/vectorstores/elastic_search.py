from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import os
from dotenv import load_dotenv

from .base_search import BaseSearchService

# Load environment variables
load_dotenv()

# Import settings
from src.app.core.config import settings
from src.app.services.embedding_factory.embedding_factory import EmbeddingFactory

DEFAULT_ES_URL = (
    f"{settings.ELASTICSEARCH_SCHEME}://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"
)


class ElasticSearchService(BaseSearchService):
    """Elasticsearch implementation of search service"""

    def __init__(
        self,
        hosts: List[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        cloud_id: Optional[str] = None,
        embedding_provider: str = None,
        embedding_model: str = None,
    ):
        """
        Initialize Elasticsearch client

        Args:
            hosts: List of Elasticsearch host URLs (default: from ELASTIC_HOSTS env or localhost:9200)
            username: Basic auth username (default: from ELASTIC_USERNAME env)
            password: Basic auth password (default: from ELASTIC_PASSWORD env)
            api_key: API key for authentication (default: from ELASTIC_API_KEY env)
            cloud_id: Elastic Cloud ID (default: from ELASTIC_CLOUD_ID env)
            embedding_provider: Embedding provider ('openai' or 'bedrock')
            embedding_model: Embedding model name
        """
        # Load from environment variables if not provided
        if hosts is None:
            endpoint = os.getenv("ELASTIC_SEARCH_ENDPOINT")
            hosts = [endpoint] if endpoint else [DEFAULT_ES_URL]
        if username is None:
            username = os.getenv("ELASTIC_USERNAME")
        if password is None:
            password = os.getenv("ELASTIC_PASSWORD")
        if embedding_provider is None:
            embedding_provider = os.getenv("EMBEDDING_PROVIDER", settings.EMBEDDING_PROVIDER)
        if embedding_model is None:
            embedding_model = os.getenv("EMBEDDING_MODEL", settings.EMBEDDING_MODEL)

        # Initialize Elasticsearch client
        if api_key and hosts:
            # Using API key with endpoint URL
            self.client = Elasticsearch(hosts=hosts, api_key=api_key)
        elif username and password:
            self.client = Elasticsearch(
                "https://localhost:9200",
                basic_auth=("elastic", "elastic"),
                ca_certs=settings.ELASTIC_CERT_PATH
            )
        else:
            self.client = Elasticsearch(hosts=hosts or [DEFAULT_ES_URL])

        # Initialize embedding provider
        self.embedder = EmbeddingFactory.create(embedding_provider, embedding_model)

    def create_index(
        self,
        index_name: str,
        mappings: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Create an index with mappings and settings

        Args:
            index_name: Name of the index
            mappings: Index mappings configuration
            settings: Index settings configuration (ignored in serverless mode)

        Returns:
            bool: True if successful
        """
        try:
            body = {"mappings": mappings}
            # Only add settings if not in serverless mode
            if settings:
                # Try with settings first
                try:
                    body["settings"] = settings
                    self.client.indices.create(index=index_name, body=body)
                except Exception as e:
                    if "serverless" in str(e).lower():
                        # Retry without settings for serverless
                        body = {"mappings": mappings}
                        self.client.indices.create(index=index_name, body=body)
                    else:
                        raise
            else:
                self.client.indices.create(index=index_name, body=body)
            return True
        except Exception as e:
            error_str = str(e)
            if "resource_already_exists_exception" in error_str:
                print(f"Index '{index_name}' already exists, skipping creation")
                return True  # Not an error - index exists
            print(f"Error creating index: {e}")
            return False

    def delete_index(self, index_name: str) -> bool:
        """
        Delete an index

        Args:
            index_name: Name of the index to delete

        Returns:
            bool: True if successful
        """
        try:
            self.client.indices.delete(index=index_name)
            print(f"Index '{index_name}' deleted successfully")
            return True
        except Exception as e:
            print(f"Error deleting index: {e}")
            return False

    def index_exists(self, index_name: str) -> bool:
        """
        Check if an index exists

        Args:
            index_name: Name of the index to check

        Returns:
            bool: True if index exists
        """
        try:
            return self.client.indices.exists(index=index_name)
        except Exception as e:
            print(f"Error checking index existence: {e}")
            return False

    def get_document_count(self, index_name: str) -> int:
        """
        Get the number of documents in an index

        Args:
            index_name: Name of the index

        Returns:
            int: Number of documents, -1 on error
        """
        try:
            response = self.client.count(index=index_name)
            return response["count"]
        except Exception as e:
            print(f"Error getting document count: {e}")
            return -1

    def clear_index(self, index_name: str) -> bool:
        """
        Delete all documents from an index without deleting the index itself

        Args:
            index_name: Name of the index to clear

        Returns:
            bool: True if successful
        """
        try:
            response = self.client.delete_by_query(
                index=index_name, body={"query": {"match_all": {}}}
            )
            deleted_count = response.get("deleted", 0)
            print(f"Cleared {deleted_count} documents from index '{index_name}'")
            return True
        except Exception as e:
            print(f"Error clearing index: {e}")
            return False

    def create_vector_index(
        self,
        index_name: str,
        text_fields: List[str],
        vector_field: str = "embedding",
        vector_dims: int = None,
    ) -> bool:
        """
        Create an index optimized for vector search with text fields

        Args:
            index_name: Name of the index
            text_fields: List of text field names
            vector_field: Name of the vector field
            vector_dims: Dimensionality of vectors (1024 for text-embedding-ada-002, 1536 for Titan)

        Returns:
            bool: True if successful
        """
        if vector_dims is None:
            vector_dims = settings.VECTOR_DIMENSIONS
            
        mappings = {
            "properties": {
                vector_field: {
                    "type": "dense_vector",
                    "dims": vector_dims,
                    "index": True,
                    "similarity": "cosine",
                }
            }
        }

        # Add text fields
        for field in text_fields:
            mappings["properties"][field] = {"type": "text"}

        # Don't set shards/replicas settings - let Elasticsearch/serverless handle it
        return self.create_index(index_name, mappings, settings=None)

    def index_document(
        self, index_name: str, document: Dict[str, Any], doc_id: Optional[str] = None
    ) -> bool:
        """
        Index a single document

        Args:
            index_name: Name of the index
            document: Document to index
            doc_id: Optional document ID

        Returns:
            bool: True if successful
        """
        try:
            if doc_id:
                self.client.index(index=index_name, id=doc_id, document=document)
            else:
                self.client.index(index=index_name, document=document)
            return True
        except Exception as e:
            print(f"Error indexing document: {e}")
            return False

    def bulk_index(self, index_name: str, documents: List[Dict[str, Any]]) -> bool:
        """
        Bulk index multiple documents

        Args:
            index_name: Name of the index
            documents: List of documents to index

        Returns:
            bool: True if successful
        """
        try:
            actions = []
            for doc in documents:
                actions.append({"_index": index_name, "_source": doc})

            success_count, errors = bulk(self.client, actions, raise_on_error=False)

            if errors:
                print("\nBulk indexing completed with errors:")
                print(f"  Successfully indexed: {success_count} documents")
                print(f"  Failed: {len(errors)} documents")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"    Error: {error}")
                return False
            else:
                print(f"Successfully indexed {success_count} documents")
                return True

        except Exception as e:
            print(f"Error bulk indexing: {e}")
            return False

    def full_text_search(
        self, index_name: str, query: str, fields: List[str], size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Full-text search using BM25

        Args:
            index_name: Name of the index
            query: Search query text
            fields: Fields to search in
            size: Number of results to return

        Returns:
            List of search results with scores
        """
        try:
            search_query = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": fields,
                        "type": "best_fields",
                    }
                },
                "size": size,
            }

            response = self.client.search(index=index_name, body=search_query)

            results = []
            for hit in response["hits"]["hits"]:
                results.append(
                    {"id": hit["_id"], "score": hit["_score"], "source": hit["_source"]}
                )

            return results
        except Exception as e:
            print(f"Error in full-text search: {e}")
            return []

    def vector_search(
        self,
        index_name: str,
        vector: List[float],
        vector_field: str,
        size: int = 10,
        num_candidates: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Vector similarity search using kNN

        Args:
            index_name: Name of the index
            vector: Query vector
            vector_field: Name of the vector field
            size: Number of results to return
            num_candidates: Number of candidates for kNN

        Returns:
            List of search results with scores
        """
        try:
            search_query = {
                "knn": {
                    "field": vector_field,
                    "query_vector": vector,
                    "k": size,
                    "num_candidates": num_candidates,
                }
            }

            response = self.client.search(index=index_name, body=search_query)

            results = []
            for hit in response["hits"]["hits"]:
                results.append(
                    {"id": hit["_id"], "score": hit["_score"], "source": hit["_source"]}
                )

            return results
        except Exception as e:
            print(f"Error in vector search: {e}")
            return []

    def hybrid_search(
        self,
        index_name: str,
        query: str,
        vector: List[float],
        text_fields: List[str],
        vector_field: str,
        text_weight: float = 0.5,
        vector_weight: float = 0.5,
        size: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining BM25 and vector similarity using script_score

        Args:
            index_name: Name of the index
            query: Search query text
            vector: Query vector
            text_fields: Fields to search for text
            vector_field: Name of the vector field
            text_weight: Weight for BM25 score
            vector_weight: Weight for vector score
            size: Number of results to return

        Returns:
            List of search results with combined scores
        """
        try:
            # Hybrid search using script_score to combine BM25 and vector similarity
            search_query = {
                "size": size,
                "query": {
                    "script_score": {
                        "query": {
                            "multi_match": {"query": query, "fields": text_fields}
                        },
                        "script": {
                            "source": f"""
                                double textScore = _score * {text_weight};
                                double vectorScore = cosineSimilarity(params.query_vector, '{vector_field}') * {vector_weight};
                                return textScore + vectorScore;
                            """,
                            "params": {"query_vector": vector},
                        },
                    }
                },
            }

            response = self.client.search(index=index_name, body=search_query)

            results = []
            for hit in response["hits"]["hits"]:
                results.append(
                    {"id": hit["_id"], "score": hit["_score"], "source": hit["_source"]}
                )

            return results
        except Exception as e:
            print(f"Error in hybrid search: {e}")
            return []

    def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for text using the configured embedding provider.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        return self.embedder.embed(text)

    def close(self):
        """Close the Elasticsearch connection"""
        if self.client:
            self.client.close()
