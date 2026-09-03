import streamlit as st
import requests
import os
import time

# Page Configuration - Minimal & Clean
st.set_page_config(
    page_title="DocuSense RAG",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# High-Contrast, Minimalist Custom CSS
st.markdown("""
<style>
    /* Global Page Styling */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Sidebar Fixes: High-contrast readable text */
    section[data-testid="stSidebar"] {
        background-color: #1E293B !important;
        border-right: 1px solid #334155 !important;
    }
    
    section[data-testid="stSidebar"] *, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color: #F1F5F9 !important;
    }
    
    /* Typography */
    h1, h2, h3, h4 {
        color: #F8FAFC !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    
    .subtitle {
        color: #94A3B8;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    /* Input Field Styling */
    .stTextInput > div > div > input {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25) !important;
    }

    /* Button Styling */
    .stButton > button {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: background-color 0.2s ease-in-out !important;
    }
    
    .stButton > button:hover {
        background-color: #1D4ED8 !important;
    }

    /* Clean Answer Display Card */
    .answer-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 20px;
        margin-top: 10px;
        margin-bottom: 20px;
        color: #F8FAFC;
        line-height: 1.6;
        font-size: 1.05rem;
    }

    /* Citation Source Card */
    .citation-card {
        background-color: #1E293B;
        border-left: 4px solid #3B82F6;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    
    .citation-header {
        color: #60A5FA;
        font-weight: 600;
        font-size: 0.88rem;
        margin-bottom: 6px;
    }
    
    .citation-body {
        color: #E2E8F0;
        font-size: 0.92rem;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

# API Endpoint URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

# App Header
st.title("DocuSense RAG Q&A")
st.markdown('<p class="subtitle">Ask questions over uploaded PDF/DOCX documents with cited sources.</p>', unsafe_allow_html=True)

# Sidebar Controls
with st.sidebar:
    st.title("📄 Document Center")
    st.markdown("Upload documents to build your vector search index.")
    
    uploaded_files = st.file_uploader(
        "Upload PDF or DOCX files",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_key = f"uploaded_{uploaded_file.name}"
            if file_key not in st.session_state:
                with st.spinner(f"Sending {uploaded_file.name}..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        response = requests.post(f"{API_URL}/upload", files=files, timeout=10)
                        
                        if response.status_code == 202:
                            data = response.json()
                            st.session_state[file_key] = data["task_id"]
                            st.success(f"Enqueued: {uploaded_file.name}")
                        else:
                            st.error(f"Upload failed: {response.text}")
                    except Exception as e:
                        st.error(f"Cannot connect to server: {e}")
                        
    st.divider()
    
    st.subheader("⚙️ Search Configuration")
    use_hybrid = st.toggle("Hybrid Search (FAISS + BM25)", value=True, help="Combines semantic vector search with keyword search using RRF ranking.")
    k_chunks = st.slider("Context Chunks (Top-K)", min_value=1, max_value=10, value=4)
    
    st.divider()
    
    # System Status Check
    st.subheader("🟢 System Readiness")
    try:
        health_resp = requests.get(f"{API_URL}/health", timeout=3)
        if health_resp.status_code == 200:
            health = health_resp.json()
            if health.get("status") == "ok":
                st.success("Backend API & Redis: Healthy")
            else:
                st.warning("Backend API Online (Dependencies degraded)")
        else:
            st.error("Backend Status Degraded")
    except Exception:
        st.error("Backend Disconnected")

# Main Interface
st.subheader("Search & Ask Questions")
question = st.text_input("Enter your question:", placeholder="e.g., What is the termination clause notice period?")

if st.button("Ask DocuSense"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Searching document index..."):
            try:
                payload = {
                    "question": question,
                    "hybrid": use_hybrid,
                    "k": k_chunks
                }
                
                start_time = time.time()
                response = requests.post(f"{API_URL}/query", json=payload, timeout=30)
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                    
                    # Display Answer
                    st.markdown("#### Answer")
                    st.markdown(f'<div class="answer-card">{answer}</div>', unsafe_allow_html=True)
                    st.caption(f"Retrieved and generated in {elapsed:.2f} seconds.")
                    
                    # Display Sources / Citations
                    st.markdown("#### Cited Passages")
                    if not sources:
                        st.info("No text passages were retrieved matching this query.")
                        if "cannot find the answer" in answer.lower():
                            st.warning(
                                "💡 **Why no results?** If you uploaded a document recently, please verify that your "
                                "`OPENAI_API_KEY` in `.env` is valid and has active credit balance. "
                                "If the API key is missing or quota is exhausted (`credit_balance_exhausted`), document embeddings cannot be generated. "
                                "Check worker logs using: `docker-compose logs -f worker`."
                            )
                    else:
                        for idx, source in enumerate(sources):
                            src_name = source.get("source", "unknown")
                            page_or_section = source.get("page")
                            content = source.get("content", "")
                            
                            st.markdown(f"""
                            <div class="citation-card">
                                <div class="citation-header">[{idx + 1}] {src_name} (Page/Section: {page_or_section})</div>
                                <div class="citation-body">"{content}"</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                elif response.status_code == 429:
                    st.error("⚠️ Rate limit exceeded! Too many requests submitted per minute. Please wait before asking again.")
                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")
                    
            except Exception as e:
                st.error(f"Could not submit query: {e}")
