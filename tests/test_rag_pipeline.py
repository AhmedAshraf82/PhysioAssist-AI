"""
Comprehensive test for the RAG pipeline: Index Creation -> Indexing -> Search
Tests the complete flow from creating an index to searching documents.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.app.services.index_creation import IndexCreationService
from src.app.services.indexer import IndexerService
from src.app.services.rag_service import RAGService
from src.app.vectorstores.sample_data import get_sample_documents
from src.app.core.config import settings


def test_index_creation():
    """Test 1: Create a new index"""
    print("\n" + "="*80)
    print("TEST 1: INDEX CREATION")
    print("="*80)
    
    index_service = IndexCreationService(search_service_type="elasticsearch")
    index_name = "test_physio_injuries"
    
    # Delete index if it exists
    if index_service.index_exists(index_name):
        print(f"⚠️  Index '{index_name}' already exists. Deleting...")
        index_service.delete_index(index_name)
    
    # Create new index
    print(f"\nCreating index: {index_name}")
    print(f"Vector dimensions: {settings.VECTOR_DIMENSIONS}")
    print(f"Embedding model: {settings.EMBEDDING_MODEL}")
    print(f"Embedding provider: {settings.EMBEDDING_PROVIDER}")
    
    success = index_service.create_index(
        index_name=index_name,
        vector_dimensions=settings.VECTOR_DIMENSIONS,
        text_fields=["title", "content", "tags"]
    )
    
    if success:
        print("✅ Index created successfully!")
        
        # Verify index exists
        exists = index_service.index_exists(index_name)
        print(f"✅ Index verification: {'EXISTS' if exists else 'MISSING'}")
        
        # Check document count (should be 0)
        count = index_service.get_document_count(index_name)
        print(f"📊 Document count: {count}")
        
        return index_name
    else:
        print("❌ Failed to create index!")
        return None


def test_indexing(index_name: str):
    """Test 2: Index sample documents"""
    print("\n" + "="*80)
    print("TEST 2: DOCUMENT INDEXING")
    print("="*80)
    
    # Load sample documents
    sample_docs = get_sample_documents()
    print(f"\n📚 Loaded {len(sample_docs)} sample documents")
    
    # Initialize indexer service
    indexer = IndexerService(search_service_type="elasticsearch")
    
    # Index documents
    print(f"\n🔄 Starting indexing process...")
    stats = indexer.index_chunks(index_name=index_name, chunks=sample_docs)
    
    # Display results
    print("\n📊 Indexing Statistics:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  ✅ Indexed: {stats['indexed_count']}")
    print(f"  ❌ Failed: {stats['failed_count']}")
    
    if stats['errors']:
        print(f"\n⚠️  Errors encountered:")
        for error in stats['errors'][:5]:  # Show first 5 errors
            print(f"    - {error}")
    
    # Verify indexing
    index_service = IndexCreationService(search_service_type="elasticsearch")
    final_count = index_service.get_document_count(index_name)
    print(f"\n📊 Final document count in index: {final_count}")
    
    if final_count == len(sample_docs):
        print("✅ All documents indexed successfully!")
        return True
    else:
        print(f"⚠️  Expected {len(sample_docs)} documents but found {final_count}")
        return False


def test_search(index_name: str):
    """Test 3: Search functionality"""
    print("\n" + "="*80)
    print("TEST 3: SEARCH FUNCTIONALITY")
    print("="*80)
    
    # Initialize RAG service
    rag_service = RAGService(search_service_type="elasticsearch")
    
    # Test queries
    test_queries = [
        {
            "query": "neck pain and numbness in arm",
            "description": "Cervical injury symptoms"
        },
        {
            "query": "shoulder weakness and pain at night",
            "description": "Shoulder injury symptoms"
        },
        {
            "query": "elbow pain with gripping",
            "description": "Elbow injury symptoms"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{'─'*80}")
        print(f"Test Query {i}: {test_case['description']}")
        print(f"Query: '{test_case['query']}'")
        print(f"{'─'*80}")
        
        # Test 3a: Full-text search (BM25)
        print("\n🔍 Full-Text Search (BM25):")
        try:
            results = rag_service.full_text_search(
                index_name=index_name,
                query=test_case['query'],
                fields=["title", "content"],
                size=3
            )
            print(f"  Found {len(results)} results")
            for j, result in enumerate(results, 1):
                print(f"  {j}. {result['source']['title']} (score: {result['score']:.4f})")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Test 3b: Vector search
        print("\n🔍 Vector Search:")
        try:
            results = rag_service.vector_search(
                index_name=index_name,
                query=test_case['query'],
                size=3
            )
            print(f"  Found {len(results)} results")
            for j, result in enumerate(results, 1):
                print(f"  {j}. {result['source']['title']} (score: {result['score']:.4f})")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Test 3c: Hybrid search
        print("\n🔍 Hybrid Search (BM25 + Vector):")
        try:
            results = rag_service.hybrid_search(
                index_name=index_name,
                query=test_case['query'],
                text_fields=["title", "content"],
                size=3
            )
            print(f"  Found {len(results)} results")
            for j, result in enumerate(results, 1):
                print(f"  {j}. {result['source']['title']} (score: {result['score']:.4f})")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n✅ Search tests completed!")


def test_cleanup(index_name: str):
    """Test 4: Cleanup (optional)"""
    print("\n" + "="*80)
    print("TEST 4: CLEANUP")
    print("="*80)
    
    response = input(f"\nDo you want to delete the test index '{index_name}'? (y/n): ")
    
    if response.lower() == 'y':
        index_service = IndexCreationService(search_service_type="elasticsearch")
        success = index_service.delete_index(index_name)
        if success:
            print(f"✅ Index '{index_name}' deleted successfully!")
        else:
            print(f"❌ Failed to delete index '{index_name}'")
    else:
        print(f"ℹ️  Index '{index_name}' kept for further testing")


def main():
    """Run all tests in sequence"""
    print("\n" + "="*80)
    print("RAG PIPELINE COMPREHENSIVE TEST")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Search Service: elasticsearch")
    print(f"  Embedding Provider: {settings.EMBEDDING_PROVIDER}")
    print(f"  Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"  Vector Dimensions: {settings.VECTOR_DIMENSIONS}")
    print(f"  Index Name: {settings.INDEX_NAME}")
    
    try:
        # Test 1: Create index
        index_name = test_index_creation()
        if not index_name:
            print("\n❌ Test failed at index creation. Aborting.")
            return
        
        # Test 2: Index documents
        if not test_indexing(index_name):
            print("\n⚠️  Indexing completed with issues, but continuing...")
        
        # Small delay to allow indexing to complete
        import time
        print("\n⏳ Waiting 2 seconds for indexing to complete...")
        time.sleep(2)
        
        # Test 3: Search
        test_search(index_name)
        
        # Test 4: Cleanup
        test_cleanup(index_name)
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
