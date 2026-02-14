from typing import List, Dict, Any, Optional
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
import os
from dotenv import load_dotenv
from .base_search import BaseSearchService
from src.app.core.config import settings
from opensearchpy.exceptions import RequestError
from src.app.services.embedding_factory.embedding_factory import EmbeddingFactory

# Load environment variables
load_dotenv()

DEFAULT_OPENSEARCH_URL = (
    f"{settings.OPENSEARCH_SCHEME}://{settings.OPENSEARCH_HOST}:{settings.OPENSEARCH_PORT}"
)


class OpenSearchService(BaseSearchService):
    """OpenSearch implementation of search service"""

    def __init__(
        self,
        hosts: Optional[List[str]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        cloud_id: Optional[str] = None,
        embedding_provider: str = None,
        embedding_model: str = None,
    ):
        """
        Initialize OpenSearch client

        Args:
            hosts: List of OpenSearch host URLs
            username: Basic auth username
            password: Basic auth password
            api_key: API key for authentication
            cloud_id: Cloud ID (if applicable)
            embedding_provider: Embedding provider ('openai' or 'bedrock')
            embedding_model: Embedding model name
        """
        # Load from environment if not provided
        if hosts is None:
            endpoint = os.getenv("OPENSEARCH_ENDPOINT")
            hosts = [endpoint] if endpoint else [DEFAULT_OPENSEARCH_URL]
        if username is None:
            username = os.getenv("OPENSEARCH_USERNAME")
        if password is None:
            password = os.getenv("OPENSEARCH_PASSWORD")
        if api_key is None:
            api_key = os.getenv("OPENSEARCH_API_KEY")
        if embedding_provider is None:
            embedding_provider = os.getenv("EMBEDDING_PROVIDER", settings.EMBEDDING_PROVIDER)
        if embedding_model is None:
            embedding_model = os.getenv("EMBEDDING_MODEL", settings.EMBEDDING_MODEL)

        # Initialize OpenSearch client
        if api_key and hosts:
            self.client = OpenSearch(hosts=hosts, api_key=api_key)
        elif username and password:
            self.client = OpenSearch(
                hosts=[{"host": settings.OPENSEARCH_HOST, "port": settings.OPENSEARCH_PORT}],
                http_auth=(username, password),
                use_ssl=True,
                verify_certs=True,
                ca_certs=settings.OPENSEARCH_CERT_PATH
            )
        else:
            self.client = OpenSearch(hosts=hosts)

        # Initialize embedding provider
        self.embedder = EmbeddingFactory.create(embedding_provider, embedding_model)

    # ------------------------- Index Management -------------------------
    def create_index(self, index_name, mappings, settings=None):
        body = {"mappings": mappings}
        if settings:
            body["settings"] = settings

        try:
            self.client.indices.create(index=index_name, body=body)
            return True
        except RequestError as e:
            if e.error == "resource_already_exists_exception":
                return True
            print(f"Error creating index: {e.info}")
            return False

    def create_vector_index(
        self,
        index_name: str,
        text_fields: List[str],
        vector_field: str = "embedding",
        vector_dims: int = None,
    ) -> bool:
        """
        Create an OpenSearch index optimized for vector search
        """
        if vector_dims is None:
            vector_dims = settings.VECTOR_DIMENSIONS

        mappings = {
            "properties": {
                vector_field: {
                    "type": "knn_vector",
                    "dimension": vector_dims,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "faiss",
                    },
                }
            }
        }

        # Add text fields
        for field in text_fields:
            mappings["properties"][field] = {"type": "text"}

        settings = {"index": {"knn": True}}

        return self.create_index(index_name, mappings, settings=settings)

    def delete_index(self, index_name: str) -> bool:
        try:
            self.client.indices.delete(index=index_name)
            return True
        except Exception as e:
            print(f"Error deleting index: {e}")
            return False

    def index_exists(self, index_name: str) -> bool:
        try:
            return self.client.indices.exists(index=index_name)
        except Exception as e:
            print(f"Error checking index existence: {e}")
            return False

    def get_document_count(self, index_name: str) -> int:
        try:
            response = self.client.count(index=index_name)
            return response["count"]
        except Exception as e:
            print(f"Error getting document count: {e}")
            return -1

    def clear_index(self, index_name: str) -> bool:
        try:
            self.client.delete_by_query(
                index=index_name, body={"query": {"match_all": {}}}
            )
            return True
        except Exception as e:
            print(f"Error clearing index: {e}")
            return False

    # ------------------------- Document Indexing -------------------------
    def index_document(
        self, index_name: str, document: Dict[str, Any], doc_id: Optional[str] = None
    ) -> bool:
        try:
            if doc_id:
                self.client.index(index=index_name, id=doc_id, body=document, refresh=True)
            else:
                self.client.index(index=index_name, body=document)
            return True
        except Exception as e:
            print(f"Error indexing document: {e}")
            return False

    def bulk_index(self, index_name: str, documents: List[Dict[str, Any]]) -> bool:
        try:
            actions = [{"_index": index_name, "_source": doc} for doc in documents]
            success_count, errors = bulk(self.client, actions, raise_on_error=False)
            if errors:
                print(
                    f"Bulk indexing completed with errors ({len(errors)}): {errors[:3]}"
                )
                return False
            return True
        except Exception as e:
            print(f"Error bulk indexing: {e}")
            return False

    # ------------------------- Search -------------------------
    def full_text_search(
        self, index_name: str, query: str, fields: List[str], size: int = 10
    ) -> List[Dict[str, Any]]:
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
            return [
                {"id": hit["_id"], "score": hit["_score"], "source": hit["_source"]}
                for hit in response["hits"]["hits"]
            ]
        except Exception as e:
            print(f"Error in full-text search: {e}")
            return []

    def vector_search(
        self,
        index_name: str,
        vector: List[float],
        vector_field: str,
        size: int = 10,
    ) -> List[Dict[str, Any]]:
        try:
            search_query = {
                "size": size,
                "query": {
                    "knn": {
                        vector_field: {
                            "vector": vector,
                            "k": size,
                        }
                    }
                },
            }
            response = self.client.search(index=index_name, body=search_query)
            return [
                {"id": hit["_id"], "score": hit["_score"], "source": hit["_source"]}
                for hit in response["hits"]["hits"]
            ]
        except Exception as e:
            print(f"Error in vector search: {e}")
            return []
        
    def hybrid_search(self, index_name, query, vector, text_fields, vector_field, text_weight=0.5, vector_weight=0.5, size=10):
        # BM25 search
        text_results = self.full_text_search(index_name, query, text_fields, size*2)
        text_scores = {r["id"]: r["score"] for r in text_results}

        # k-NN vector search
        vector_results = self.vector_search(index_name, vector, vector_field, size*2)
        vector_scores = {r["id"]: r["score"] for r in vector_results}

        # Merge scores
        merged_ids = set(text_scores.keys()) | set(vector_scores.keys())
        merged_results = []
        for doc_id in merged_ids:
            score = text_scores.get(doc_id, 0) * text_weight + vector_scores.get(doc_id, 0) * vector_weight
            source = next((r["source"] for r in text_results + vector_results if r["id"] == doc_id), {})
            merged_results.append({"id": doc_id, "score": score, "source": source})

        # Sort and return
        merged_results.sort(key=lambda x: x["score"], reverse=True)
        return merged_results[:size]

    # ------------------------- Embeddings -------------------------
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
        if self.client:
            self.client.close()
