import streamlit as st
import requests
import os
import time

# Page Configuration - Clean & Modern
st.set_page_config(
    page_title="DocuSense RAG",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Minimalist Theme (High Contrast & Elegant Typography)
st.markdown("""
<style>
    /* Hide default Streamlit top header & footer */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}

    /* Main App Background */
    .stApp {
        background-color: #090D16;
        color: #F8FAFC;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1E293B !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #F8FAFC !important;
        font-weight: 700 !important;
    }

    /* File Uploader Custom Dark Theme */
    [data-testid="stFileUploader"] {
        background-color: #1E293B !important;
        border: 1px dashed #475569 !important;
        border-radius: 10px !important;
        padding: 12px !important;
    }
    
    [data-testid="stFileUploader"] * {
        color: #94A3B8 !important;
    }

    /* Headings */
    h1, h2, h3, h4 {
        color: #F8FAFC !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .subtitle {
        color: #94A3B8;
        font-size: 0.98rem;
        margin-bottom: 1.8rem;
    }

    /* Question Input Box */
    .stTextInput > div > div > input {
        background-color: #111827 !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        padding: 14px 18px !important;
        font-size: 1rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2) !important;
    }

    /* Ask Button */
    .stButton > button {
        background: linear-gradient(135deg, #0284C7 0%, #2563EB 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35) !important;
    }

    /* Answer Card Container */
    .answer-card {
        background-color: #111827;
        border: 1px solid #1E293B;
        border-left: 4px solid #38BDF8;
        border-radius: 10px;
        padding: 22px;
        margin-top: 10px;
        margin-bottom: 24px;
        color: #F8FAFC;
        line-height: 1.7;
        font-size: 1.02rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    /* Citation Passages Card */
    .citation-card {
        background-color: #111827;
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    
    .citation-badge {
        display: inline-block;
        background-color: #1E293B;
        color: #38BDF8;
        font-weight: 700;
        font-size: 0.82rem;
        padding: 4px 10px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    
    .citation-text {
        color: #CBD5E1;
        font-size: 0.93rem;
        line-height: 1.6;
        font-style: italic;
    }

    /* Guidance Box */
    .notice-card {
        background-color: #1E1B4B;
        border: 1px solid #3730A3;
        border-radius: 8px;
        padding: 16px 20px;
        color: #C7D2FE;
        font-size: 0.92rem;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# API Endpoint URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

# App Header
st.markdown('<div class="main-title">DocuSense RAG</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask questions over uploaded PDF/DOCX documents with cited sources.</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
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
    
    st.divider()
    
    # Backend Status
    st.markdown("### 🟢 System Status")
    try:
        health_resp = requests.get(f"{API_URL}/health", timeout=3)
        if health_resp.status_code == 200:
            health = health_resp.json()
            if health.get("status") == "ok":
                st.success("Backend & Services Online")
            else:
                st.warning("Backend Online (Degraded services)")
        else:
            st.error("Backend Degraded")
    except Exception:
        st.error("Backend Disconnected")

# Main Interface
st.markdown("### Search & Ask Questions")
question = st.text_input("Question:", placeholder="e.g., What is the dress code for the convocation?", label_visibility="collapsed")

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
                        if "cannot find the answer" in answer.lower():
                            st.markdown("""
                            <div class="notice-card">
                                💡 <b>Setup Tip:</b> If your answer was not found, check your <code>.env</code> file to ensure 
                                <code>GEMINI_API_KEY</code> contains your free Google AI Studio key (starts with <code>AIzaSy...</code>). 
                                Free local embeddings (HuggingFace) have successfully processed your document!
                            </div>
                            """, unsafe_allow_html=True)
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
