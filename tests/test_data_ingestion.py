"""
Tests for data ingestion pipeline.
Tests both the pipeline logic and the API endpoints.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.app.services.data_ingestion_pipeline import DataIngestionPipeline, run_ingestion_pipeline
from src.app.core.config import settings


def test_pipeline_initialization():
    """Test 1: Pipeline initialization"""
    print("\n" + "="*80)
    print("TEST 1: PIPELINE INITIALIZATION")
    print("="*80)
    
    try:
        pipeline = DataIngestionPipeline()
        print("✅ Pipeline initialized successfully")
        print(f"  Search service: {pipeline.search_service_type}")
        print(f"  Embedding provider: {pipeline.embedding_provider}")
        print(f"  Embedding model: {pipeline.embedding_model}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize pipeline: {e}")
        return False


def test_index_info():
    """Test 2: Get index information"""
    print("\n" + "="*80)
    print("TEST 2: INDEX INFO")
    print("="*80)
    
    try:
        pipeline = DataIngestionPipeline()
        info = pipeline.get_index_info("test_pipeline_index")
        
        print(f"✅ Retrieved index info:")
        print(f"  Index name: {info['index_name']}")
        print(f"  Exists: {info['exists']}")
        if info['exists']:
            print(f"  Document count: {info['document_count']}")
        print(f"  Vector dimensions: {info.get('vector_dimensions', 'N/A')}")
        print(f"  Embedding provider: {info.get('embedding_provider', 'N/A')}")
        print(f"  Embedding model: {info.get('embedding_model', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to get index info: {e}")
        return False


def test_full_pipeline():
    """Test 3: Run complete ingestion pipeline"""
    print("\n" + "="*80)
    print("TEST 3: FULL PIPELINE EXECUTION")
    print("="*80)
    
    index_name = "test_ingestion_pipeline"
    
    try:
        # Run pipeline with recreate flag to ensure clean start
        print(f"\nRunning pipeline for index: {index_name}")
        results = run_ingestion_pipeline(
            index_name=index_name,
            recreate_index=True
        )
        
        print("\n📊 Pipeline Results:")
        print(f"  Success: {results['success']}")
        print(f"  Message: {results['message']}")
        print(f"  Index name: {results['index_name']}")
        print(f"  Index created: {results['index_created']}")
        print(f"  Index existed: {results['index_existed']}")
        print(f"  Documents fetched: {results['documents_fetched']}")
        print(f"  Documents indexed: {results['documents_indexed']}")
        print(f"  Documents failed: {results['documents_failed']}")
        
        if results['errors']:
            print(f"\n⚠️  Errors:")
            for error in results['errors']:
                print(f"    - {error}")
        
        if results['success']:
            print("\n✅ Pipeline executed successfully!")
            
            # Verify with index info
            pipeline = DataIngestionPipeline()
            info = pipeline.get_index_info(index_name)
            print(f"\n📊 Verification:")
            print(f"  Index exists: {info['exists']}")
            print(f"  Document count: {info['document_count']}")
            
            return True
        else:
            print(f"\n❌ Pipeline failed: {results['message']}")
            return False
            
    except Exception as e:
        print(f"\n❌ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_with_existing_index():
    """Test 4: Run pipeline with existing index (no recreate)"""
    print("\n" + "="*80)
    print("TEST 4: PIPELINE WITH EXISTING INDEX")
    print("="*80)
    
    index_name = "test_ingestion_pipeline"
    
    try:
        # Run without recreate flag
        print(f"\nRunning pipeline for existing index: {index_name}")
        results = run_ingestion_pipeline(
            index_name=index_name,
            recreate_index=False
        )
        
        print("\n📊 Pipeline Results:")
        print(f"  Success: {results['success']}")
        print(f"  Message: {results['message']}")
        print(f"  Index existed: {results['index_existed']}")
        print(f"  Index created: {results['index_created']}")
        print(f"  Documents indexed: {results['documents_indexed']}")
        
        if results['index_existed'] and not results['index_created']:
            print("\n✅ Pipeline correctly used existing index!")
            return True
        else:
            print("\n⚠️  Unexpected behavior with existing index")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


def test_cleanup():
    """Test 5: Cleanup test index"""
    print("\n" + "="*80)
    print("TEST 5: CLEANUP")
    print("="*80)
    
    index_name = "test_ingestion_pipeline"
    
    response = input(f"\nDo you want to delete the test index '{index_name}'? (y/n): ")
    
    if response.lower() == 'y':
        try:
            from src.app.services.index_creation import IndexCreationService
            index_service = IndexCreationService()
            success = index_service.delete_index(index_name)
            
            if success:
                print(f"✅ Index '{index_name}' deleted successfully!")
            else:
                print(f"⚠️  Failed to delete index '{index_name}'")
                
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
    else:
        print(f"ℹ️  Index '{index_name}' kept for further testing")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("DATA INGESTION PIPELINE TESTS")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Search Service: {settings.SEARCH_SERVICE_TYPE}")
    print(f"  Embedding Provider: {settings.EMBEDDING_PROVIDER}")
    print(f"  Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"  Default Index: {settings.INDEX_NAME}")
    
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    tests = [
        ("Initialization", test_pipeline_initialization),
        ("Index Info", test_index_info),
        ("Full Pipeline", test_full_pipeline),
        ("Existing Index", test_pipeline_with_existing_index),
    ]
    
    for test_name, test_func in tests:
        results["total"] += 1
        try:
            if test_func():
                results["passed"] += 1
            else:
                results["failed"] += 1
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results["failed"] += 1
    
    # Cleanup
    test_cleanup()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total tests: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    
    if results['failed'] == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {results['failed']} test(s) failed")
    
    print("="*80)


if __name__ == "__main__":
    main()
