"""
PhysioAssist AI - Streamlit Frontend
Main chat interface with search and data ingestion capabilities.
"""

import streamlit as st
import requests
import uuid
import base64
from datetime import datetime
from typing import List, Dict, Any
import os

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8002")
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
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "last_reply_audio_bytes" not in st.session_state:
    st.session_state.last_reply_audio_bytes = None
if "last_reply_audio_mime" not in st.session_state:
    st.session_state.last_reply_audio_mime = None
if "wa_numbers" not in st.session_state:
    st.session_state.wa_numbers = []


def get_or_create_user_id() -> str:
    """Get a stable browser user_id using query params fallback."""
    if st.session_state.user_id:
        return st.session_state.user_id

    qp = st.query_params
    qp_user_id = qp.get("uid")
    if qp_user_id:
        st.session_state.user_id = str(qp_user_id)
        return st.session_state.user_id

    generated = f"web_{uuid.uuid4()}"
    st.session_state.user_id = generated
    st.query_params["uid"] = generated
    return generated


def load_chat_history(chat_id: str) -> List[Dict[str, Any]]:
    """Load chat history from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/prediagnose/{chat_id}/history", timeout=90)
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


def send_message(message: str, chat_id: str = None, user_id: str = None) -> Dict[str, Any]:
    """Send message to prediagnose endpoint."""
    try:
        payload = {"message": message}
        if chat_id:
            payload["chat_id"] = chat_id
        if user_id:
            payload["user_id"] = user_id
        
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


def send_multimodal_message(
    message: str = "",
    chat_id: str = None,
    user_id: str = None,
    uploaded_file=None,
) -> Dict[str, Any]:
    """Send text and/or media to multimodal prediagnose endpoint."""
    try:
        data = {}
        if message:
            data["message"] = message
        if chat_id:
            data["chat_id"] = chat_id
        if user_id:
            data["user_id"] = user_id

        files = None
        if uploaded_file is not None:
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type or "application/octet-stream",
                )
            }

        response = requests.post(
            f"{API_BASE_URL}/prediagnose/multimodal",
            data=data,
            files=files,
            timeout=90,
        )

        if response.status_code == 200:
            return response.json()

        try:
            detail = response.json().get("detail", "")
        except Exception:
            detail = ""
        st.error(f"Error: {response.status_code} {detail}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to API server")
        return None
    except Exception as e:
        st.error(f"Failed to send multimodal message: {str(e)[:100]}")
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
        response = requests.get(f"{API_BASE_URL}/prediagnose/sessions", timeout=90)
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


def delete_session(chat_id: str) -> bool:
    """Delete a single chat session."""
    try:
        response = requests.delete(f"{API_BASE_URL}/prediagnose/{chat_id}", timeout=30)
        return response.status_code == 200
    except Exception:
        return False


def clear_all_sessions() -> int:
    """Delete all chat sessions and return deleted count."""
    try:
        response = requests.delete(f"{API_BASE_URL}/prediagnose/sessions/all", timeout=30)
        if response.status_code == 200:
            return int(response.json().get("deleted_count", 0))
        return 0
    except Exception:
        return 0


def check_api_health() -> bool:
    """Check if API server is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=90)
        return response.status_code == 200
    except:
        return False


def get_latest_user_session(user_id: str) -> Dict[str, Any] | None:
    """Get latest session for a user from API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/prediagnose/user/{user_id}/latest",
            timeout=30,
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def send_whatsapp_bulk_message(numbers: List[str], message: str) -> Dict[str, Any] | None:
    """Send a text message to multiple WhatsApp numbers via backend endpoint."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/webhooks/whatsapp/send-text",
            json={"numbers": numbers, "message": message},
            timeout=90,
        )

        if response.status_code == 200:
            return response.json()

        try:
            detail = response.json().get("detail", "")
        except Exception:
            detail = response.text
        st.error(f"WhatsApp send failed: {response.status_code} {detail}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to API server")
        return None
    except Exception as e:
        st.error(f"Failed to send WhatsApp message: {str(e)[:100]}")
        return None


# Header
st.markdown('<h1 class="main-header">🏥 PhysioAssist AI</h1>', unsafe_allow_html=True)

# Ensure stable user id
get_or_create_user_id()

# Check API health
api_status = check_api_health()
if not api_status:
    st.error("🔴 **API Server is not running!** Please start the FastAPI server:")
    # Check if we're in Docker (API_BASE_URL will be set to backend service)
    if "backend" in API_BASE_URL:
        st.code("Backend container is not responding. Check: podman logs physioassist-backend", language="bash")
    else:
        st.code("uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8002", language="bash")
    st.stop()
else:
    st.success("🟢 API Server Connected")

# Restore latest session on first app load/reopen for this user
if not st.session_state.chat_id:
    latest_session = get_latest_user_session(st.session_state.user_id)
    if latest_session and latest_session.get("chat_id"):
        st.session_state.chat_id = latest_session["chat_id"]
        st.session_state.messages = load_chat_history(st.session_state.chat_id)

st.markdown("---")

# Sidebar for controls
with st.sidebar:
    st.header("⚙️ Controls")

    st.subheader("📲 WhatsApp Sender")
    wa_number_input = st.text_input(
        "Add phone number",
        placeholder="201090253864",
        help="Use 201... format. +201... and 01... are accepted and normalized by backend.",
    )
    if st.button("➕ Add Number", use_container_width=True):
        candidate = (wa_number_input or "").strip()
        if not candidate:
            st.warning("Please enter a number")
        elif candidate in st.session_state.wa_numbers:
            st.info("Number already added")
        else:
            st.session_state.wa_numbers.append(candidate)

    if st.session_state.wa_numbers:
        st.caption("Recipients")
        for idx, number in enumerate(st.session_state.wa_numbers):
            col_num, col_remove = st.columns([5, 1])
            with col_num:
                st.write(number)
            with col_remove:
                if st.button("✖", key=f"wa_remove_{idx}"):
                    st.session_state.wa_numbers.pop(idx)
                    st.rerun()

        wa_message = st.text_area(
            "WhatsApp message",
            placeholder="Type message to send...",
            height=80,
            key="wa_bulk_message",
        )
        if st.button("📤 Send WhatsApp Message", use_container_width=True):
            if not wa_message.strip():
                st.warning("Please enter a message")
            else:
                with st.spinner("Sending WhatsApp message(s)..."):
                    result = send_whatsapp_bulk_message(st.session_state.wa_numbers, wa_message.strip())
                if result:
                    st.success(
                        f"Status: {result.get('status')} | sent: {result.get('sent_count', 0)} | failed: {result.get('failed_count', 0)}"
                    )

    st.markdown("---")
    
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

        if st.button("🗑️ Clear All Sessions", use_container_width=True, type="secondary"):
            deleted_count = clear_all_sessions()
            if deleted_count > 0:
                st.success(f"Deleted {deleted_count} sessions")
            else:
                st.info("No sessions deleted")
            st.session_state.chat_id = None
            st.session_state.messages = []
            st.rerun()

        for session in sessions[:5]:  # Show last 5 sessions
            chat_id = session.get("chat_id", "")
            msg_count = session.get("message_count", 0)
            col_view, col_delete = st.columns([5, 1])
            with col_view:
                if st.button(
                    f"📝 {chat_id[:8]}... ({msg_count} msgs)",
                    key=f"open_{chat_id}",
                    use_container_width=True,
                ):
                    st.session_state.chat_id = chat_id
                    st.session_state.messages = load_chat_history(chat_id)
                    st.rerun()
            with col_delete:
                if st.button("🗑️", key=f"del_{chat_id}", use_container_width=True):
                    if delete_session(chat_id):
                        if st.session_state.chat_id == chat_id:
                            st.session_state.chat_id = None
                            st.session_state.messages = []
                        st.success("Session deleted")
                    else:
                        st.error("Failed to delete session")
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

    if st.session_state.last_reply_audio_bytes:
        st.caption("Last voice reply")
        st.audio(
            st.session_state.last_reply_audio_bytes,
            format=st.session_state.last_reply_audio_mime or "audio/ogg",
        )
    
    # Unified Chat input (text + browse file + voice recording)
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Your message:",
            placeholder="Describe your symptoms or ask a question...",
            height=100,
        )

        uploaded_media = st.file_uploader(
            "Attach file (image/audio)",
            type=["jpg", "jpeg", "png", "webp", "ogg", "mp3", "wav", "m4a"],
            accept_multiple_files=False,
            key="chat_media_uploader",
            help="You can upload an image or a voice/audio file.",
        )

        recorded_audio = st.audio_input("Or record a voice note")

        submitted = st.form_submit_button("Send 📤", use_container_width=True)

        if submitted:
            message_text = user_input.strip()

            if uploaded_media is not None and recorded_audio is not None:
                st.info("Both uploaded and recorded audio detected. Using the recorded voice note.")

            selected_media = recorded_audio if recorded_audio is not None else uploaded_media

            if not message_text and selected_media is None:
                st.warning("Please add text, attach a file, or record a voice note.")
            else:
                with st.spinner("Thinking..."):
                    response = send_multimodal_message(
                        message=message_text,
                        chat_id=st.session_state.chat_id,
                        user_id=st.session_state.user_id,
                        uploaded_file=selected_media,
                    )

                    if response:
                        reply_audio_base64 = response.get("reply_audio_base64")
                        reply_audio_mime_type = response.get("reply_audio_mime_type")

                        if reply_audio_base64:
                            try:
                                st.session_state.last_reply_audio_bytes = base64.b64decode(
                                    reply_audio_base64
                                )
                                st.session_state.last_reply_audio_mime = (
                                    reply_audio_mime_type or "audio/ogg"
                                )
                            except Exception:
                                st.session_state.last_reply_audio_bytes = None
                                st.session_state.last_reply_audio_mime = None
                        else:
                            st.session_state.last_reply_audio_bytes = None
                            st.session_state.last_reply_audio_mime = None

                        st.session_state.chat_id = response.get("chat_id")
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
