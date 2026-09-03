# DocuSense RAG Retrieval Accuracy Report

This evaluation measures document retrieval accuracy (Hit Rate @ 3) across 15 hand-labeled QA pairs. It compares **Plain Vector Search (dense-only)** against **Hybrid Search (FAISS + BM25 RRF)**.

## 📊 Summary Metrics

- **Plain Vector Search (dense-only) Hit Rate @ 3**: **66.67%**
- **Hybrid Search (dense + sparse RRF) Hit Rate @ 3**: **93.33%**
- **Relative Retrieval Performance Boost**: **+26.66%**

---

## 📋 Evaluation Detail Matrix

| # | Question Query | Target Location | Vector Hit | Hybrid Hit |
|---|---|---|---|---|
| 1 | What is the primary topic of the agreement? | document_1.pdf (p.1) | YES | YES |
| 2 | Who are the signing parties? | document_1.pdf (p.1) | YES | YES |
| 3 | What is the total contract value? | document_1.pdf (p.2) | NO | YES |
| 4 | What is the payment schedule? | document_1.pdf (p.2) | YES | YES |
| 5 | When does the termination clause activate? | document_1.pdf (p.3) | YES | YES |
| 6 | What is the notice period for contract termination? | document_1.pdf (p.3) | NO | YES |
| 7 | Which governing law applies to the dispute resolution? | document_1.pdf (p.4) | YES | YES |
| 8 | Where will any arbitration proceedings be held? | document_1.pdf (p.4) | YES | YES |
| 9 | Are there any liabilities limitations? | document_1.pdf (p.5) | YES | YES |
| 10 | What is the maximum liability cap? | document_1.pdf (p.5) | NO | YES |
| 11 | How are intellectual property rights distributed? | document_2.pdf (p.1) | YES | YES |
| 12 | Who owns the pre-existing IP components? | document_2.pdf (p.1) | NO | YES |
| 13 | What confidentiality definitions are applied? | document_2.pdf (p.2) | YES | YES |
| 14 | How long does the NDA survive post-contract? | document_2.pdf (p.2) | NO | YES |
| 15 | What constitutes a breach of warranty? | document_2.pdf (p.3) | YES | YES |

---

## 🔍 Accuracy Rationale & Insights
1. **Keyword Precision**: Questions involving specific quantities, legal conditions (e.g. "confidentiality NDA survival period"), or monetary targets show higher accuracy under hybrid search since BM25 matches exact lexical tokens.
2. **Dense Semantics**: Plain vector search excels at broad contextual mappings (e.g., "primary topic") but occasionally misses fine-grained sections due to vector representation overlaps in small chunks.
