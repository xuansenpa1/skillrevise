# SWE-Skills-Bench: rag-implementation (batch9)

# Task: Build a RAG Pipeline with Hybrid Search and Reranking in LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) needs a production-grade RAG (Retrieval-Augmented Generation) pipeline that combines dense and sparse retrieval (hybrid search), applies reranking for improved precision, handles document chunking with metadata preservation, and provides source citations in the generated answer. The pipeline must be modular and testable without requiring live LLM/embedding API calls.

## Files to Create/Modify

- `libs/langchain/langchain/rag/chunker.py` (create) — `DocumentChunker` class that splits documents into overlapping chunks while preserving section headers, code blocks, and metadata
- `libs/langchain/langchain/rag/hybrid_retriever.py` (create) — `HybridRetriever` class that combines dense (vector similarity) and sparse (BM25) retrieval with weighted reciprocal rank fusion
- `libs/langchain/langchain/rag/reranker.py` (create) — `CrossEncoderReranker` class that reranks retrieved documents using a cross-encoder scoring model (with a mock implementation for testing)
- `libs/langchain/langchain/rag/pipeline.py` (create) — `RAGPipeline` class that orchestrates chunking → indexing → hybrid retrieval → reranking → answer generation with source citations
- `libs/langchain/langchain/rag/citation.py` (create) — `CitationExtractor` class that parses LLM responses and maps claims to source document chunks
- `libs/tests/unit_tests/test_rag_pipeline.py` (create) — Tests for each component using mock embeddings and LLM responses

## Requirements

### Document Chunker (`chunker.py`)

- Class `DocumentChunker` accepts: `chunk_size` (int, default 512 tokens), `chunk_overlap` (int, default 64 tokens), `separators` (list[str], default `["\n## ", "\n### ", "\n\n", "\n", " "]`)
- Method `chunk(documents: list[Document]) -> list[Document]` where each input `Document` has `page_content` (str) and `metadata` (dict with `source`, `title`)
- Splitting strategy: try each separator in order; split at the first separator that produces chunks fitting within `chunk_size`
- Each output chunk's metadata must include: original `source`, `title`, `chunk_index` (int), `start_char` (int), `end_char` (int), and `parent_section` (str, the nearest preceding `##` or `###` heading)
- Code blocks (triple backtick) must never be split mid-block; if a code block exceeds `chunk_size`, keep it as a single oversized chunk
- Overlap: the last `chunk_overlap` tokens of chunk N must be duplicated as the first tokens of chunk N+1

### Hybrid Retriever (`hybrid_retriever.py`)

- Class `HybridRetriever` accepts: `dense_retriever` (callable returning list[tuple[Document, float]]), `sparse_retriever` (callable returning list[tuple[Document, float]]), `dense_weight` (float, default 0.6), `sparse_weight` (float, default 0.4), `top_k` (int, default 20)
- Method `retrieve(query: str) -> list[tuple[Document, float]]` — Calls both retrievers, fuses results using Reciprocal Rank Fusion (RRF):
  - For each document in dense results at rank `i`: `score += dense_weight * 1/(k + i)` where `k=60`
  - For each document in sparse results at rank `j`: `score += sparse_weight * 1/(k + j)` where `k=60`
  - Documents appearing in both lists get both scores summed
  - Return top `top_k` documents sorted by fused score descending
- Document identity is determined by `metadata["source"]` + `metadata["chunk_index"]`

### Reranker (`reranker.py`)

- Class `CrossEncoderReranker` accepts: `model_fn` (callable taking `(query, document_text) -> float` score), `top_n` (int, default 5)
- Method `rerank(query: str, documents: list[tuple[Document, float]]) -> list[tuple[Document, float]]` — Scores each document using `model_fn(query, doc.page_content)`, returns top `top_n` sorted by cross-encoder score descending
- If `model_fn` is None, use a fallback: score based on word overlap between query and document (Jaccard similarity)

### RAG Pipeline (`pipeline.py`)

- Class `RAGPipeline` accepts: `chunker` (DocumentChunker), `retriever` (HybridRetriever), `reranker` (CrossEncoderReranker), `llm_fn` (callable taking prompt string, returns response string), `prompt_template` (str with `{context}` and `{question}` placeholders)
- Method `index(documents: list[Document])` — Chunks documents and stores them for retrieval
- Method `query(question: str) -> dict` — Returns `{"answer": str, "sources": list[dict], "context_documents": list[Document]}` where:
  1. Retrieves documents via hybrid retriever
  2. Reranks to top N
  3. Formats context from reranked documents into the prompt template
  4. Calls `llm_fn` with the formatted prompt
  5. Extracts citations from the response
  6. `sources` contains `[{"source": str, "title": str, "chunk_index": int, "relevance_score": float}]`

### Citation Extractor (`citation.py`)

- Class `CitationExtractor` accepts: `source_documents` (list[Document])
- Method `extract(response: str) -> list[dict]` — Finds text spans in the response that can be attributed to source chunks using longest common substring matching (minimum 20 characters). Returns `[{"claim": str, "source": str, "chunk_index": int, "confidence": float}]` where confidence = `len(match) / len(claim)`

### Expected Functionality

- Chunking a 2000-token document with chunk_size=512 and overlap=64 produces 4–5 chunks
- Hybrid retrieval with documents scored [0.9, 0.8, 0.7] by dense and [0.85, 0.75] by sparse produces correct RRF fusion scores
- Reranking reorders documents based on cross-encoder scores, potentially promoting a dense rank-5 document to rank-1
- Full pipeline query returns an answer with source citations linking claims to specific chunks

## Acceptance Criteria

- `DocumentChunker` preserves code blocks intact and includes `parent_section` metadata
- `HybridRetriever` correctly implements RRF with configurable dense/sparse weights
- Documents appearing in both dense and sparse results receive summed RRF scores
- `CrossEncoderReranker` reorders documents by model score, falling back to Jaccard similarity
- `RAGPipeline` orchestrates the full flow from question to cited answer
- `CitationExtractor` maps response text back to source documents with confidence scores
- All components work with mock functions (no live API calls required for testing)
- `python -m pytest /workspace/tests/test_rag_implementation.py -v --tb=short` passes
