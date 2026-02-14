"""
RAG Tool for searching indexed migration templates.

This tool provides RAG-based search functionality that can be used across
multiple agent teams and group chats.
"""

from autogen_core.tools import FunctionTool
from src.app.services.rag_service import RAGService
from src.app.core.config import settings

# Initialize RAG service (shared instance)
_rag_service = RAGService(search_service_type=settings.SEARCH_SERVICE_TYPE)


# ============================================================================
# RAG SEARCH FUNCTION
# ============================================================================

def rag(query: str) -> str:
    """
    Search indexed physiotherapy information using RAG.
    
    Args:
        query: Search query like "What are effective exercises for lower back pain?"
        
    Returns:
        Relevant physiotherapy information based on the query, or an error message if search fails.
    """
    try:
        results = _rag_service.hybrid_search(
            index_name=settings.INDEX_NAME,
            query=query,
            text_fields=["title", "content", "tags"],
            vector_field="embedding",
            text_weight=0.5,
            vector_weight=0.5,
            size=settings.RAG_TOP_K
        )
         
        if not results:
            return "No physiotherapy information found for this query. Please check the query or ensure relevant data is indexed."
        
        top_result = results[0]
        source = top_result.get('source', {})
        title = source.get('title', 'Physiotherapy Information')
        content = source.get('content', '')
        
        return f"# {title}\n\n{content}"
        
    except Exception as e:
        return f"Error searching migration templates: {str(e)}"


# ============================================================================
# AUTOGEN FUNCTION TOOL
# ============================================================================

rag_search_tool = FunctionTool(
    name="rag",
    description=(
        "Retrieve relevant physiotherapy information based on a search query. "
    ),
    func=rag
)
