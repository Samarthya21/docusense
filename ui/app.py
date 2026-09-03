import streamlit as st
import requests
import os
import time

# Page Config with a dark modern aesthetic
st.set_page_config(
    page_title="DocuSense - Production RAG Q&A",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply premium modern custom CSS styles
st.markdown("""
<style>
    /* Base Container Styling */
    .stApp {
        background-color: #0B0F19;
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Title and Header Typography */
    h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 50%, #1D4ED8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    
    /* Sidebar Layout Styling */
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1F2937;
    }
    
    /* Styled Answer Display Container */
    .answer-box {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    
    /* Citation tags inside the text */
    .citation {
        background-color: #1E3A8A;
        color: #93C5FD;
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 0.2rem;
    }

    /* Customized Cards for Citation Sources */
    .source-card {
        background-color: #1F2937;
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid #3B82F6;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .source-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.1);
    }
    
    .source-header {
        font-size: 0.85rem;
        font-weight: 700;
        color: #60A5FA;
        margin-bottom: 0.4rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .source-body {
        font-size: 0.9rem;
        color: #D1D5DB;
        line-height: 1.5;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# Fetch backend API URL from environment
API_URL = os.getenv("API_URL", "http://localhost:8000")

# App Header
st.title("DocuSense RAG Q&A")
st.markdown("Retrieval-Augmented Generation system over PDFs & DOCXs with dense-sparse hybrid search.")

# Sidebar Configuration Layout
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/000000/documents.png", width=100)
    st.header("Upload Center")
    uploaded_files = st.file_uploader(
        "Upload PDF/DOCX Documents",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_key = f"uploaded_{uploaded_file.name}"
            if file_key not in st.session_state:
                with st.spinner(f"Ingesting {uploaded_file.name}..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        response = requests.post(f"{API_URL}/upload", files=files, timeout=10)
                        
                        if response.status_code == 202:
                            data = response.json()
                            st.session_state[file_key] = data["task_id"]
                            st.toast(f"✅ Enqueued {uploaded_file.name}! Task ID: {data['task_id'][:8]}...", icon="📥")
                        else:
                            st.error(f"Failed to upload {uploaded_file.name}: {response.text}")
                    except Exception as e:
                        st.error(f"Error connecting to backend: {e}")
        
    st.divider()
    st.header("Search Parameters")
    use_hybrid = st.toggle("Enable Hybrid Search", value=True, help="Fuses dense FAISS search and sparse BM25 search using Reciprocal Rank Fusion.")
    k_chunks = st.slider("Top-k Chunks (Context size)", min_value=1, max_value=10, value=4)
    
    st.divider()
    # Health Indicators
    st.subheader("System Health")
    try:
        health_resp = requests.get(f"{API_URL}/health", timeout=3)
        if health_resp.status_code == 200:
            health = health_resp.json()
            if health.get("status") == "ok":
                st.success("🟢 All services online")
            else:
                st.warning("⚠️ Component issue detected")
        else:
            st.error("🔴 Offline")
    except Exception:
        st.error("🔴 Offline (No connection)")

# Main Query Panel
st.subheader("Interactive Query Interface")
question = st.text_input("Ask a question about the uploaded documents:", placeholder="e.g., What are the terms of the agreement?")

if st.button("Ask DocuSense", type="primary"):
    if not question.strip():
        st.warning("Please type a valid question.")
    else:
        with st.spinner("Analyzing context and generating answer..."):
            try:
                payload = {
                    "question": question,
                    "hybrid": use_hybrid,
                    "k": k_chunks
                }
                
                # Execute REST call
                start_time = time.time()
                response = requests.post(f"{API_URL}/query", json=payload, timeout=30)
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                    
                    # 1. Answer Card
                    st.markdown("### Answer")
                    st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)
                    st.caption(f"Generated in {elapsed:.2f} seconds")
                    
                    # 2. Citation details Card
                    st.divider()
                    st.markdown("### Cited Document Passages")
                    if not sources:
                        st.info("No sources retrieved for this answer.")
                    else:
                        for idx, source in enumerate(sources):
                            src_name = source.get("source", "unknown")
                            page_or_section = source.get("page")
                            content = source.get("content", "")
                            
                            st.markdown(f"""
                            <div class="source-card">
                                <div class="source-header">[{idx + 1}] {src_name} - Page/Section: {page_or_section}</div>
                                <div class="source-body">"{content}"</div>
                            </div>
                            """, unsafe_allow_html=True)
                elif response.status_code == 429:
                    st.error("⚠️ Rate limit exceeded! You have submitted too many requests recently. Please wait a minute and retry.")
                else:
                    st.error(f"API Error: Status {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Failed to submit query. Could not connect to API server: {e}")
