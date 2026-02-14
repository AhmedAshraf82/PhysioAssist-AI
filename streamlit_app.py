"""
PhysioAssist AI - Streamlit Frontend
Main chat interface with search and data ingestion capabilities.
"""

import streamlit as st
import requests
import uuid
from datetime import datetime
from typing import List, Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8001"
DEFAULT_USER_ID = "default_user"

# Page config
st.set_page_config(
    page_title="PhysioAssist AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .search-results {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .chat-message {
        padding: 1.2rem;
        border-radius: 0.8rem;
        margin: 0.8rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: right;
        margin-left: 15%;
    }
    .assistant-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        text-align: left;
        margin-right: 15%;
    }
    .timestamp {
        font-size: 0.8rem;
        color: rgba(255,255,255,0.8);
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "chat_id" not in st.session_state:
    st.session_state.chat_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []


def load_chat_history(chat_id: str) -> List[Dict[str, Any]]:
    """Load chat history from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/prediagnose/{chat_id}/history", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("history", [])
        return []
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to API server")
        return []
    except Exception as e:
        st.error(f"Failed to load history: {str(e)[:100]}")
        return []


def send_message(message: str, chat_id: str = None) -> Dict[str, Any]:
    """Send message to prediagnose endpoint."""
    try:
        payload = {"message": message}
        if chat_id:
            payload["chat_id"] = chat_id
        
        response = requests.post(
            f"{API_BASE_URL}/prediagnose",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to API server")
        return None
    except Exception as e:
        st.error(f"Failed to send message: {str(e)[:100]}")
        return None


def search_injuries(query: str) -> List[Dict[str, Any]]:
    """Search for injuries using hybrid search."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/search/",
            json={"query": query}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
        return []
    except Exception as e:
        st.error(f"Search failed: {e}")
        return []


def trigger_ingestion(recreate_index: bool = False) -> Dict[str, Any]:
    """Trigger data ingestion pipeline."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/data/ingest",
            json={"recreate_index": recreate_index}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ingestion failed: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Failed to trigger ingestion: {e}")
        return None


def list_sessions() -> List[Dict[str, Any]]:
    """List all chat sessions."""
    try:
        response = requests.get(f"{API_BASE_URL}/prediagnose/sessions", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("sessions", [])
        return []
    except requests.exceptions.ConnectionError:
        st.sidebar.error("⚠️ API server not running")
        return []
    except requests.exceptions.Timeout:
        st.sidebar.warning("⏱️ Request timeout")
        return []
    except Exception as e:
        st.sidebar.error(f"Error: {str(e)[:50]}")
        return []


def check_api_health() -> bool:
    """Check if API server is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


# Header
st.markdown('<h1 class="main-header">🏥 PhysioAssist AI</h1>', unsafe_allow_html=True)

# Check API health
api_status = check_api_health()
if not api_status:
    st.error("🔴 **API Server is not running!** Please start the FastAPI server:")
    st.code("uvicorn src.main:app --reload --host 0.0.0.0 --port 8001", language="bash")
    st.stop()
else:
    st.success("🟢 API Server Connected")

st.markdown("---")

# Sidebar for controls
with st.sidebar:
    st.header("⚙️ Controls")
    
    # Data Ingestion Section
    st.subheader("📊 Data Management")
    recreate_index = st.checkbox("Recreate Index", value=False)
    if st.button("🔄 Run Data Ingestion", use_container_width=True):
        with st.spinner("Running ingestion pipeline..."):
            result = trigger_ingestion(recreate_index)
            if result and result.get("success"):
                st.success(f"✅ {result.get('message')}")
                st.info(f"Documents: {result.get('documents_indexed')}/{result.get('documents_fetched')}")
            else:
                st.error("❌ Ingestion failed")
    
    st.markdown("---")
    
    # Chat Session Management
    st.subheader("💬 Chat Sessions")
    if st.button("🆕 New Chat", use_container_width=True):
        st.session_state.chat_id = None
        st.session_state.messages = []
        st.rerun()
    
    # List existing sessions
    sessions = list_sessions()
    if sessions:
        st.write(f"**Active Sessions:** {len(sessions)}")
        for session in sessions[:5]:  # Show last 5 sessions
            chat_id = session.get("chat_id", "")
            msg_count = session.get("message_count", 0)
            if st.button(f"📝 {chat_id[:8]}... ({msg_count} msgs)", key=chat_id, use_container_width=True):
                st.session_state.chat_id = chat_id
                st.session_state.messages = load_chat_history(chat_id)
                st.rerun()
    
    st.markdown("---")
    
    # Session info
    if st.session_state.chat_id:
        st.info(f"**Current Session:**\n`{st.session_state.chat_id[:16]}...`")
    else:
        st.warning("No active session")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Chat with PhysioAssist")
    
    # Load chat history on first load
    if st.session_state.chat_id and not st.session_state.messages:
        st.session_state.messages = load_chat_history(st.session_state.chat_id)
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        if st.session_state.messages:
            for msg in st.session_state.messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                
                if role == "user":
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You:</strong> {content}
                        <div class="timestamp">{timestamp}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>PhysioAssist:</strong> {content}
                        <div class="timestamp">{timestamp}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("👋 Start a conversation! Ask me about injuries, symptoms, or treatments.")
    
    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Your message:", placeholder="Describe your symptoms or ask a question...", height=100)
        submitted = st.form_submit_button("Send 📤", use_container_width=True)
        
        if submitted and user_input:
            # Send message
            with st.spinner("Thinking..."):
                response = send_message(user_input, st.session_state.chat_id)
                
                if response:
                    # Update session
                    st.session_state.chat_id = response.get("chat_id")
                    
                    # Reload messages
                    st.session_state.messages = load_chat_history(st.session_state.chat_id)
                    st.rerun()

with col2:
    st.header("🔍 Search Injuries")
    
    # Search input
    with st.form("search_form"):
        search_query = st.text_input("Search:", placeholder="e.g., neck pain, shoulder injury...")
        search_button = st.form_submit_button("Search 🔎", use_container_width=True)
        
        if search_button and search_query:
            with st.spinner("Searching..."):
                st.session_state.search_results = search_injuries(search_query)
    
    # Display search results
    if st.session_state.search_results:
        st.subheader(f"Results ({len(st.session_state.search_results)})")
        
        for idx, result in enumerate(st.session_state.search_results, 1):
            score = result.get("score", 0)
            document = result.get("document", {})
            title = document.get("title", "Untitled")
            content = document.get("content", "")
            tags = document.get("tags", [])
            
            with st.expander(f"**{idx}. {title}** (Score: {score:.2f})"):
                st.markdown(f"**Tags:** {', '.join(tags)}")
                st.markdown("---")
                st.markdown(content)
    else:
        st.info("🔎 Use the search bar above to find injury information")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    PhysioAssist AI © 2026 | Powered by FastAPI + Streamlit
</div>
""", unsafe_allow_html=True)
