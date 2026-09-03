import streamlit as st
import requests
import os
import time

# Page Config
st.set_page_config(
    page_title="DocuSense RAG",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast CSS Fixes
st.markdown("""
<style>
    /* Hide Streamlit default header elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}

    /* Base App Styling */
    .stApp {
        background-color: #090D16;
        color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Sidebar Layout */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1E293B !important;
    }
    
    section[data-testid="stSidebar"] *, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] p {
        color: #F1F5F9 !important;
    }

    /* FIX FILE UPLOADER WHITE BACKGROUND */
    [data-testid="stFileUploader"], 
    [data-testid="stFileUploader"] > div, 
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploaderDropzone"] {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px dashed #475569 !important;
        border-radius: 8px !important;
    }
    
    [data-testid="stFileUploader"] small, 
    [data-testid="stFileUploader"] span, 
    [data-testid="stFileUploader"] p {
        color: #CBD5E1 !important;
    }

    [data-testid="stFileUploader"] button {
        background-color: #334155 !important;
        color: #F8FAFC !important;
        border: 1px solid #475569 !important;
        border-radius: 6px !important;
    }

    /* FIX INVISIBLE PLACEHOLDER TEXT */
    .stTextInput > div > div > input {
        background-color: #111827 !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #94A3B8 !important;
        opacity: 1 !important;
    }
    
    .stTextInput > div > div > input::-webkit-input-placeholder {
        color: #94A3B8 !important;
        opacity: 1 !important;
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #38BDF8;
        margin-bottom: 0.2rem;
    }
    
    .subtitle {
        color: #94A3B8;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    /* Buttons */
    .stButton > button {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    /* Cards */
    .answer-card {
        background-color: #111827;
        border: 1px solid #1E293B;
        border-left: 4px solid #38BDF8;
        border-radius: 8px;
        padding: 18px;
        margin-top: 8px;
        margin-bottom: 18px;
        color: #F8FAFC;
        line-height: 1.6;
    }

    .citation-card {
        background-color: #111827;
        border: 1px solid #1E293B;
        border-radius: 6px;
        padding: 14px;
        margin-bottom: 10px;
    }
    
    .citation-badge {
        color: #38BDF8;
        font-weight: 700;
        font-size: 0.85rem;
        margin-bottom: 6px;
    }
    
    .citation-text {
        color: #CBD5E1;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# API Endpoint URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Main Page Header
st.markdown('<div class="main-title">DocuSense RAG</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask questions over uploaded PDF/DOCX documents with cited sources.</div>', unsafe_allow_html=True)

# Sidebar Layout (Moved System Status to TOP so it is immediately visible!)
with st.sidebar:
    st.markdown("### 🟢 System Status")
    try:
        health_resp = requests.get(f"{API_URL}/health", timeout=3)
        if health_resp.status_code == 200:
            health = health_resp.json()
            if health.get("status") == "ok":
                st.success("Backend Services: Online")
            else:
                st.warning("Backend Services: Degraded")
        else:
            st.error("Backend Degraded")
    except Exception:
        st.error("Backend Disconnected")
        
    st.divider()

    st.markdown("### 📄 Document Upload")
    uploaded_files = st.file_uploader(
        "Drop PDF or DOCX files here",
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
                            st.success(f"Enqueued: {uploaded_file.name}")
                        else:
                            st.error(f"Upload failed: {response.text}")
                    except Exception as e:
                        st.error(f"Cannot connect to backend: {e}")
                        
    st.divider()
    
    st.markdown("### ⚙️ Search Settings")
    use_hybrid = st.toggle("Hybrid Search (FAISS + BM25)", value=True, help="Combines vector search with keyword search using RRF ranking.")
    k_chunks = st.slider("Context Chunks (Top-K)", min_value=1, max_value=10, value=4)

# Main Query Section
st.markdown("### Search & Ask Questions")
question = st.text_input(
    "Enter your question:", 
    placeholder="e.g., What is the dress code for the convocation?",
    key="user_question"
)

if st.button("Ask DocuSense"):
    if not question.strip():
        st.warning("Please type a question.")
    else:
        with st.spinner("Searching documents & generating answer..."):
            try:
                payload = {
                    "question": question,
                    "hybrid": use_hybrid,
                    "k": k_chunks
                }
                
                start_time = time.time()
                response = requests.post(f"{API_URL}/query", json=payload, timeout=45)
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                    
                    # Output Answer Card
                    st.markdown("#### Answer")
                    st.markdown(f'<div class="answer-card">{answer}</div>', unsafe_allow_html=True)
                    st.caption(f"Retrieved and generated in {elapsed:.2f} seconds.")
                    
                    # Output Citations / Sources
                    st.markdown("#### Cited Passages")
                    if not sources:
                        st.info("No matching text passages were found.")
                    else:
                        for idx, source in enumerate(sources):
                            src_name = source.get("source", "unknown")
                            page_or_section = source.get("page")
                            content = source.get("content", "")
                            
                            st.markdown(f"""
                            <div class="citation-card">
                                <div class="citation-badge">[{idx + 1}] {src_name} — Page/Section: {page_or_section}</div>
                                <div class="citation-text">"{content}"</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                elif response.status_code == 429:
                    st.error("⚠️ Rate limit exceeded! Please wait 1 minute before submitting another query.")
                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")
                    
            except Exception as e:
                st.error(f"Failed to submit query: {e}")
