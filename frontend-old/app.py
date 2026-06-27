import streamlit as st
import requests
import time
import os
from pathlib import Path
from typing import List, Dict, Any

# Configure Page
st.set_page_config(
    page_title="LAIKA - Local AI Knowledge Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
BACKEND_URL = os.getenv("LAIKA_API_URL", "http://localhost:8080").rstrip("/")

# Load Custom Premium Styles
st.markdown("""
<style>
    /* Google Fonts Import */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Space+Grotesk:wght@400;600&display=swap');
    
    /* Variables & General Styling */
    :root {
        --primary-glow: radial-gradient(rgba(102, 252, 241, 0.15), rgba(102, 252, 241, 0));
        --neon-cyan: #66FCF1;
        --neon-purple: #8A2BE2;
        --glass-bg: rgba(25, 30, 41, 0.65);
        --glass-border: rgba(102, 252, 241, 0.12);
        --text-primary: #F5F7FA;
    }
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0A0B10 0%, #121520 100%);
        color: var(--text-primary);
    }
    
    /* Title Shadow Effect */
    .glowing-title {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 800;
        letter-spacing: 2px;
        background: linear-gradient(90deg, #66FCF1 0%, #A370F7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(102, 252, 241, 0.3);
        margin-bottom: 0px;
    }
    
    .sub-title {
        font-size: 1.1rem;
        color: #8F9CAE;
        font-weight: 300;
        margin-bottom: 2rem;
    }

    /* Sidebar Glassmorphic Box */
    [data-testid="stSidebar"] {
        background-color: rgba(10, 11, 16, 0.85);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-indexed {
        background-color: rgba(46, 204, 113, 0.15);
        color: #2ecc71;
        border: 1px solid rgba(46, 204, 113, 0.3);
    }
    .badge-uploading {
        background-color: rgba(241, 196, 15, 0.15);
        color: #f1c40f;
        border: 1px solid rgba(241, 196, 15, 0.3);
        animation: pulse 1.5s infinite alternate;
    }
    .badge-error {
        background-color: rgba(231, 76, 60, 0.15);
        color: #e74c3c;
        border: 1px solid rgba(231, 76, 60, 0.3);
    }
    
    @keyframes pulse {
        0% { opacity: 0.6; }
        100% { opacity: 1; }
    }

    /* Message Bubbles styling */
    .chat-bubble-container {
        display: flex;
        margin-bottom: 1.25rem;
        width: 100%;
    }
    
    .chat-bubble {
        padding: 1rem 1.25rem;
        border-radius: 18px;
        max-width: 80%;
        line-height: 1.5;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .bubble-user {
        background: linear-gradient(135deg, #1f2538 0%, #161b29 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        color: #E2E8F0;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    
    .bubble-assistant {
        background: rgba(26, 32, 48, 0.5);
        border: 1px solid var(--glass-border);
        border-left: 3px solid var(--neon-cyan);
        color: #F7FAFC;
        margin-right: auto;
        border-top-left-radius: 4px;
    }

    /* Citation Cards Layout */
    .citation-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
        padding-left: 20px;
        margin-bottom: 12px;
    }
    
    .citation-card {
        background: rgba(102, 252, 241, 0.05);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 6px 14px;
        display: inline-flex;
        align-items: center;
        transition: all 0.25s ease;
        cursor: default;
    }
    
    .citation-card:hover {
        background: rgba(102, 252, 241, 0.1);
        border-color: var(--neon-cyan);
        box-shadow: 0 0 10px rgba(102, 252, 241, 0.15);
        transform: translateY(-1px);
    }
    
    .citation-header {
        display: flex;
        align-items: center;
        font-weight: 500;
        font-size: 0.8rem;
        color: var(--neon-cyan);
        margin-bottom: 0px;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(10, 11, 16, 0.3);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(102, 252, 241, 0.2);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(102, 252, 241, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Application state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Helper Functions
def api_get_documents() -> List[Dict[str, Any]]:
    """Fetch all document records from backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/documents", timeout=5.0)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.sidebar.error(f"Backend offline: Unable to connect to {BACKEND_URL}")
    return []

def api_upload_files(files) -> bool:
    """Upload list of files to backend API."""
    files_payload = []
    for f in files:
        files_payload.append(("files", (f.name, f.getvalue(), f.type)))
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/documents/upload", files=files_payload, timeout=10.0)
        return response.status_code == 202
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return False

def api_delete_document(doc_id: str) -> bool:
    """Delete a document by ID."""
    try:
        response = requests.delete(f"{BACKEND_URL}/api/documents/{doc_id}", timeout=5.0)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Deletion failed: {e}")
        return False

def api_retry_document(doc_id: str) -> bool:
    """Retry indexing a failed document."""
    try:
        response = requests.post(f"{BACKEND_URL}/api/documents/{doc_id}/retry", timeout=5.0)
        return response.status_code == 202
    except Exception as e:
        st.error(f"Retry failed: {e}")
        return False

def api_query_chat(
    question: str,
    history: List[Dict[str, Any]],
    top_k: int,
    score_threshold: float,
    temperature: float,
    search_mode: str
) -> Dict[str, Any]:
    """Post query to backend RAG chatbot pipeline."""
    formatted_history = []
    for turn in history:
        formatted_history.append({"role": "user", "content": turn["question"]})
        formatted_history.append({"role": "assistant", "content": turn["answer"]})
        
    payload = {
        "question": question,
        "history": formatted_history,
        "top_k": top_k,
        "score_threshold": score_threshold,
        "temperature": temperature,
        "search_mode": search_mode
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat/query",
            json=payload,
            timeout=100.0  # High timeout for local model generation
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"answer": f"Error: Backend returned status code {response.status_code}", "sources": []}
    except Exception as e:
        return {"answer": f"Connection Error: Could not reach the API backend. {e}", "sources": []}


# --- HEADER SECTION ---
col_logo, col_empty = st.columns([8, 4])
with col_logo:
    st.markdown('<h1 class="glowing-title">L A I K A</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Local AI Knowledge Assistant — Offline, Private Document Q&A</p>', unsafe_allow_html=True)


# --- SIDEBAR SECTION ---
st.sidebar.markdown('<h2 style="font-family:\'Space Grotesk\'; font-weight:600; color:#66FCF1;">🗂 Document Hub</h2>', unsafe_allow_html=True)

# Drag-and-drop file uploader
uploaded_files = st.sidebar.file_uploader(
    "Upload PDFs, DOCX, TXT, or MD files",
    type=["pdf", "docx", "txt", "md"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if uploaded_files:
    if st.sidebar.button("Process & Index Documents", use_container_width=True):
        with st.sidebar.spinner("Uploading files..."):
            success = api_upload_files(uploaded_files)
            if success:
                st.sidebar.success("Files uploaded! Indexing started.")
                st.rerun()

st.sidebar.markdown("<hr style='border-color: rgba(255,255,255,0.05);'/>", unsafe_allow_html=True)

# Advanced RAG parameters
with st.sidebar.expander("⚙️ Advanced RAG Settings", expanded=False):
    search_mode = st.selectbox(
        "Search Mode",
        options=["hybrid", "semantic", "keyword"],
        format_func=lambda x: x.capitalize(),
        index=0,
        help="Semantic uses embeddings, Keyword uses exact matches, Hybrid merges both."
    )
    top_k = st.slider(
        "Retrieve Segments (Top-K)",
        min_value=1,
        max_value=20,
        value=5,
        help="Number of document chunks to feed to the LLM."
    )
    score_threshold = st.slider(
        "Semantic Distance Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.42,
        step=0.01,
        help="Higher limits allow less matching chunks (lower is stricter)."
    )
    temperature = st.slider(
        "LLM Temperature",
        min_value=0.0,
        max_value=1.2,
        value=0.2,
        step=0.05,
        help="Controls creativity. Lower is more deterministic and factual."
    )

st.sidebar.markdown("<hr style='border-color: rgba(255,255,255,0.05);'/>", unsafe_allow_html=True)

# Active documents list
st.sidebar.markdown('<p style="font-weight:600; font-size:0.95rem; color:#8F9CAE;">Active Knowledge Bases</p>', unsafe_allow_html=True)
documents = api_get_documents()

has_uploading = False

if not documents:
    st.sidebar.info("No documents uploaded yet. Add a PDF, DOCX, TXT, or MD above to build your private knowledge assistant.")
else:
    for doc in documents:
        doc_status = doc["status"]
        if doc_status == "INDEXED":
            badge_html = f'<span class="badge badge-indexed">Indexed</span>'
        elif doc_status == "UPLOADING":
            badge_html = f'<span class="badge badge-uploading">Indexing...</span>'
            has_uploading = True
        else:
            badge_html = f'<span class="badge badge-error">Failed</span>'
            
        doc_col1, doc_col2 = st.sidebar.columns([7, 3])
        
        with doc_col1:
            short_name = doc["filename"]
            if len(short_name) > 28:
                short_name = short_name[:25] + "..."
                
            if doc.get("page_count") and doc["page_count"] > 0:
                page_text = f"{doc['page_count']} pgs"
            else:
                suffix = Path(doc["filename"]).suffix.lower().replace(".", "").upper()
                page_text = suffix if suffix else "DOC"
                
            st.markdown(
                f"<div style='font-size:0.88rem; font-weight:600; margin-bottom:2px;'>📄 {short_name}</div>"
                f"<div style='margin-bottom:8px;'>{badge_html} <span style='font-size:0.75rem; color:#6C7A89;'>• {page_text}</span></div>",
                unsafe_allow_html=True
            )
            
        with doc_col2:
            btn_col_del, btn_col_retry = st.columns(2)
            with btn_col_del:
                if st.button("🗑", key=f"del_{doc['id']}", help="Delete knowledge base"):
                    if api_delete_document(doc["id"]):
                         st.toast(f"Deleted {doc['filename']}")
                         st.rerun()
            with btn_col_retry:
                if doc_status == "ERROR":
                    if st.button("🔄", key=f"retry_{doc['id']}", help="Retry indexing"):
                        if api_retry_document(doc["id"]):
                            st.toast(f"Retrying {doc['filename']}...")
                            st.rerun()

# Auto-refresh while documents are still being indexed
if has_uploading:
    time.sleep(2)
    st.rerun()


# --- CHAT & INTERACTIVE Q&A WINDOW ---

# Display chat history
for chat in st.session_state.chat_history:
    # User message
    st.markdown(
        f'<div class="chat-bubble-container">'
        f'<div class="chat-bubble bubble-user"><b>You:</b><br/>{chat["question"]}</div>'
        f'</div>',
        unsafe_allow_html=True
    )
    
    # Assistant response
    st.markdown(
        f'<div class="chat-bubble-container">'
        f'<div class="chat-bubble bubble-assistant"><b>LAIKA:</b><br/>{chat["answer"]}</div>'
        f'</div>',
        unsafe_allow_html=True
    )
    
    # Render references/sources using clean st.expanders to see context snippets
    if chat.get("sources"):
        st.markdown("<p style='font-size:0.8rem; font-weight:600; color:#8F9CAE; margin-left: 20px; margin-bottom: 5px;'>References & Cited Context:</p>", unsafe_allow_html=True)
        for idx, src in enumerate(chat["sources"]):
            filename = src["filename"]
            page = f"Page {src['page_number']}" if src.get("page_number") and src.get("page_number") != -1 else "Text/Docx"
            
            with st.expander(f"📄 {filename} ({page})"):
                st.markdown(
                    f'<div style="font-size:0.88rem; color:#A0AEC0; border-left:3px solid #66FCF1; padding-left:10px; font-style:italic; line-height:1.4;">'
                    f'{src["text_snippet"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )
        st.markdown("<br/>", unsafe_allow_html=True)

# User Chat Input
user_query = st.chat_input("Ask a question about your uploaded documents...")

if user_query:
    st.markdown(
        f'<div class="chat-bubble-container">'
        f'<div class="chat-bubble bubble-user"><b>You:</b><br/>{user_query}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Build the request payload
    formatted_history = []
    for turn in st.session_state.chat_history:
        formatted_history.append({"role": "user", "content": turn["question"]})
        formatted_history.append({"role": "assistant", "content": turn["answer"]})

    payload = {
        "question": user_query,
        "history": formatted_history,
        "top_k": top_k,
        "score_threshold": score_threshold,
        "temperature": temperature,
        "search_mode": search_mode
    }

    # Stream tokens from the backend
    placeholder = st.empty()
    full_answer = ""

    try:
        with requests.post(
            f"{BACKEND_URL}/api/chat/query/stream",
            json=payload,
            timeout=120.0,
            stream=True
        ) as resp:
            if resp.status_code == 200:
                for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        full_answer += chunk
                        placeholder.markdown(
                            f'<div class="chat-bubble-container">'
                            f'<div class="chat-bubble bubble-assistant"><b>LAIKA:</b><br/>{full_answer}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
            else:
                # Fallback to non-streaming
                result = api_query_chat(
                    question=user_query,
                    history=st.session_state.chat_history,
                    top_k=top_k,
                    score_threshold=score_threshold,
                    temperature=temperature,
                    search_mode=search_mode
                )
                full_answer = result.get("answer", "I encountered an error querying the system.")
    except Exception as e:
        # Fallback to non-streaming on connection error
        result = api_query_chat(
            question=user_query,
            history=st.session_state.chat_history,
            top_k=top_k,
            score_threshold=score_threshold,
            temperature=temperature,
            search_mode=search_mode
        )
        full_answer = result.get("answer", f"Connection Error: {e}")

    st.session_state.chat_history.append({
        "question": user_query,
        "answer": full_answer,
        "sources": []
    })
    
    st.rerun()
