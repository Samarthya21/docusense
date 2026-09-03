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

# Custom High-Contrast, Compact & Readable CSS
st.markdown("""
<style>
    /* Hide top deploy button and decoration, BUT KEEP SIDEBAR EXPAND/COLLAPSE BUTTON VISIBLE! */
    .stDeployButton { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* Sidebar Expand/Collapse Arrow Controls Always Visible & Clear */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"],
    button[kind="header"] {
        visibility: visible !important;
        display: block !important;
        color: #F8FAFC !important;
        background-color: #1E293B !important;
        border-radius: 6px !important;
    }

    /* Base App Background */
    .stApp {
        background-color: #090D16;
        color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Compact Sidebar Layout */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1E293B !important;
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    section[data-testid="stSidebar"] *, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] p {
        color: #F1F5F9 !important;
        font-size: 0.88rem !important;
    }

    /* FIX FILE UPLOADER Styling */
    [data-testid="stFileUploader"], 
    [data-testid="stFileUploader"] > div, 
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploaderDropzone"] {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px dashed #475569 !important;
        border-radius: 8px !important;
        padding: 6px !important;
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

    /* BIGGER & HIGH VISIBILITY TYPOGRAPHY */
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #38BDF8;
        margin-bottom: 0.2rem;
    }
    
    .subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-bottom: 1.8rem;
    }

    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 1rem;
        margin-bottom: 0.8rem;
    }

    /* Input Field Styling */
    .stTextInput > div > div > input {
        background-color: #111827 !important;
        color: #F8FAFC !important;
        border: 1.5px solid #38BDF8 !important;
        border-radius: 10px !important;
        padding: 14px 18px !important;
        font-size: 1.1rem !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #94A3B8 !important;
        opacity: 1 !important;
        font-size: 1.05rem !important;
    }

    /* Action Button */
    .stButton > button {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 28px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }

    /* BIGGER ANSWER CARD */
    .answer-card {
        background-color: #111827;
        border: 1px solid #1E293B;
        border-left: 6px solid #38BDF8;
        border-radius: 10px;
        padding: 24px;
        margin-top: 10px;
        margin-bottom: 24px;
        color: #FFFFFF;
        line-height: 1.8;
        font-size: 1.2rem;
        font-weight: 500;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    .citation-card {
        background-color: #111827;
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    
    .citation-badge {
        color: #38BDF8;
        font-weight: 700;
        font-size: 0.92rem;
        margin-bottom: 6px;
    }
    
    .citation-text {
        color: #E2E8F0;
        font-size: 1rem;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# API Endpoint URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Main Page Header
st.markdown('<div class="main-title">DocuSense RAG</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask questions over uploaded PDF/DOCX documents with cited sources.</div>', unsafe_allow_html=True)

# Compact Sidebar Layout (Status -> Upload -> Settings)
with st.sidebar:
    st.markdown("#### 🟢 System Status")
    try:
        health_resp = requests.get(f"{API_URL}/health", timeout=3)
        if health_resp.status_code == 200:
            health = health_resp.json()
            if health.get("status") == "ok":
                st.success("Backend: Online")
            else:
                st.warning("Backend: Degraded")
        else:
            st.error("Backend Degraded")
    except Exception:
        st.error("Backend Disconnected")
        
    st.markdown("---")

    st.markdown("#### 📄 Document Upload")
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
                        st.error(f"Cannot connect: {e}")
                        
    st.markdown("---")
    
    st.markdown("#### ⚙️ Search Settings")
    use_hybrid = st.toggle("Hybrid Search (FAISS + BM25)", value=True, help="Combines vector search with keyword search using RRF ranking.")
    k_chunks = st.slider("Context Chunks (Top-K)", min_value=1, max_value=10, value=4)

# Main Query Section
st.markdown('<div class="section-header">Search & Ask Questions</div>', unsafe_allow_html=True)
question = st.text_input(
    "Enter your question:", 
    placeholder="e.g., What is the dress code for the convocation?",
    key="user_question",
    label_visibility="collapsed"
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
                    
                    # Output Answer Card - BIGGER & PROMINENT
                    st.markdown('<div class="section-header">Answer</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="answer-card">{answer}</div>', unsafe_allow_html=True)
                    st.caption(f"Retrieved and generated in {elapsed:.2f} seconds.")
                    
                    # Output Citations / Sources
                    st.markdown('<div class="section-header">Cited Passages</div>', unsafe_allow_html=True)
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
