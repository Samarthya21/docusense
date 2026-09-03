import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.documents import Document
from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.llm = None

    def _get_llm(self) -> ChatOpenAI:
        if not self.llm:
            # Initialize standard ChatOpenAI client
            self.llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.llm_model,
                temperature=0.0
            )
        return self.llm

    def generate_answer(self, query: str, documents: list[Document]) -> str:
        if not documents:
            return "I cannot find the answer in the provided documents."

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
            llm_client = self._get_llm()
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = llm_client.invoke(messages)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Failed to query OpenAI Chat: {e}")
            return f"Error generating answer: {e}"

llm_service = LLMService()
