import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.documents import Document
from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.llm = None

    def _get_llm(self):
        if not self.llm:
            provider = getattr(settings, "llm_provider", "gemini").lower()
            if provider == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                logger.info(f"Initializing Free Google Gemini LLM client ({settings.gemini_model})...")
                self.llm = ChatGoogleGenerativeAI(
                    google_api_key=settings.gemini_api_key,
                    model=settings.gemini_model,
                    temperature=0.0
                )
            else:
                from langchain_openai import ChatOpenAI
                logger.info(f"Initializing ChatOpenAI client ({settings.llm_model})...")
                self.llm = ChatOpenAI(
                    api_key=settings.openai_api_key,
                    model=settings.llm_model,
                    temperature=0.0
                )
        return self.llm

    def generate_answer(self, query: str, documents: list[Document]) -> str:
        if not documents:
            return "I cannot find the answer in the provided documents."

        # Check if API key is valid / present
        provider = getattr(settings, "llm_provider", "gemini").lower()
        if provider == "gemini":
            key = getattr(settings, "gemini_api_key", "").strip()
            if not key or key in ["your_free_gemini_api_key_here", "mock_key", "your_openai_api_key_here"] or key.startswith("your_"):
                return (
                    f"⚠️ Please add your free Google Gemini API key to `.env` (`GEMINI_API_KEY=...`).\n"
                    f"Get a key for $0.00 in 30 seconds at https://aistudio.google.com/app/apikey.\n\n"
                    f"Local vector search successfully found {len(documents)} matching context passages from your document!"
                )

        # Compile document contents and format headers to help the LLM cite easily
        context_blocks = []
        for idx, doc in enumerate(documents):
            source = doc.metadata.get("source", "unknown")
            page_or_section = doc.metadata.get("page") or doc.metadata.get("section") or "1"
            
            block = f"--- [Document: {source} | Page/Section: {page_or_section}] ---\n{doc.page_content}"
            context_blocks.append(block)
            
        context_text = "\n\n".join(context_blocks)
        
        system_prompt = (
            "You are a helpful assistant that answers user questions based strictly on the provided context.\n"
            "To answer, you must adhere strictly to these rules:\n"
            "1. Answer the question using ONLY the facts explicitly mentioned in the context.\n"
            "2. For every fact or claim you state, you MUST add an inline citation at the end of the sentence.\n"
            "3. Format the citation exactly as: `[Source_Filename, Page/Section]` matching the headers provided (e.g. `[manual.pdf, 5]` or `[brief.docx, Introduction]`).\n"
            "4. If the context does not contain the answer, reply exactly: 'I cannot find the answer in the provided documents.'\n"
            "5. Do NOT extrapolate or speculate. Keep answers factual and directly tied to the citations."
        )
        
        user_prompt = (
            f"Context chunks:\n{context_text}\n\n"
            f"Question: {query}\n\n"
            f"Answer:"
        )
        
        logger.info(f"Invoking LLM for query: '{query}'")
        try:
            provider = getattr(settings, "llm_provider", "gemini").lower()
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            if provider == "groq":
                from langchain_openai import ChatOpenAI
                groq_key = getattr(settings, "groq_api_key", os.getenv("GROQ_API_KEY", ""))
                logger.info("Using 100% Free Groq LLM API (llama-3.1-8b-instant)...")
                client = ChatOpenAI(
                    api_key=groq_key,
                    base_url="https://api.groq.com/openai/v1",
                    model="llama-3.1-8b-instant",
                    temperature=0.0,
                    max_retries=1,
                    request_timeout=10
                )
                response = client.invoke(messages)
            elif provider == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                models_to_try = [
                    "gemini-3.5-flash",
                    "gemini-3.6-flash",
                    "gemini-3.5-flash-lite",
                    "gemini-flash-latest"
                ]
                response = None
                last_error = None
                
                for model_name in models_to_try:
                    try:
                        logger.info(f"Trying Gemini model: '{model_name}' (timeout: 12s, max_retries: 1)...")
                        client = ChatGoogleGenerativeAI(
                            google_api_key=settings.gemini_api_key,
                            model=model_name,
                            temperature=0.0,
                            max_retries=1,
                            request_timeout=12
                        )
                        response = client.invoke(messages)
                        break
                    except Exception as err:
                        logger.warning(f"Model '{model_name}' failed/timed out ({err}). Trying next fallback model...")
                        last_error = err
                        
                if response is None:
                    raise last_error
            else:
                llm_client = self._get_llm()
                response = llm_client.invoke(messages)

            if isinstance(response.content, str):
                return response.content.strip()
            elif isinstance(response.content, list):
                text_parts = []
                for part in response.content:
                    if isinstance(part, dict):
                        text_parts.append(part.get("text", ""))
                    else:
                        text_parts.append(str(part))
                return "".join(text_parts).strip()
            return str(response.content).strip()
        except Exception as e:
            logger.error(f"Failed to query LLM: {e}")
            return (
                f"⚠️ Error calling Gemini API. Please check your `GEMINI_API_KEY` in `.env` "
                f"(Get a free key at https://aistudio.google.com/app/apikey).\n\n"
                f"Local vector search successfully found {len(documents)} matching context passages from your document!"
            )

llm_service = LLMService()
