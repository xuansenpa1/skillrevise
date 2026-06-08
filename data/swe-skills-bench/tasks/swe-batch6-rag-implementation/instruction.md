# SWE-Skills-Bench: rag-implementation (batch6)

# Task: Build a RAG System for Technical Documentation Q&A

## Background

A Retrieval-Augmented Generation system is needed for answering questions about technical documentation. The system ingests Markdown documentation files, chunks them with metadata preservation, stores embeddings in Pinecone, and uses a LangGraph-based pipeline with hybrid search (dense + BM25), reranking, and source citation. The target corpus is a set of API reference docs (~500 pages).

## Files to Create/Modify

- `src/rag/__init__.py` (create) — Package init exporting `RAGPipeline`, `DocumentIngester`, `HybridRetriever`
- `src/rag/ingestion.py` (create) — `DocumentIngester` class: load Markdown files, chunk with RecursiveCharacterTextSplitter, preserve section headings as metadata, generate embeddings, upsert to Pinecone
- `src/rag/retriever.py` (create) — `HybridRetriever` combining Pinecone dense search + BM25 sparse search with Reciprocal Rank Fusion
- `src/rag/reranker.py` (create) — Cross-encoder reranking using `cross-encoder/ms-marco-MiniLM-L-6-v2`
- `src/rag/pipeline.py` (create) — LangGraph `StateGraph` with nodes: `retrieve`, `rerank`, `generate`, `cite_sources`
- `src/rag/prompts.py` (create) — RAG prompt templates with citation instructions
- `tests/test_ingestion.py` (create) — Tests for chunking, metadata extraction, and embedding generation
- `tests/test_retriever.py` (create) — Tests for hybrid search and RRF score fusion
- `tests/test_pipeline.py` (create) — End-to-end pipeline tests with mocked LLM and vector store

## Requirements

### Document Ingestion (`src/rag/ingestion.py`)

- `DocumentIngester.__init__(index_name: str, embedding_model: str = "voyage-3-large", namespace: str = "docs")` — initialize Pinecone client and embedding model.
- `DocumentIngester.ingest_directory(path: str) -> IngestResult` — recursively load all `.md` files from a directory.
  - Chunking: `RecursiveCharacterTextSplitter` with `chunk_size=1000`, `chunk_overlap=200`, separators: `["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " "]`.
  - Metadata per chunk:
    - `source_file` — relative file path
    - `section_heading` — nearest parent heading (e.g., `"## Authentication"`)
    - `chunk_index` — sequential index within the file
    - `total_chunks` — total chunks from that file
    - `heading_hierarchy` — list of heading levels (e.g., `["# API Reference", "## Authentication", "### OAuth2"]`)
  - Embedding: batch embed chunks (max 128 per batch) using the configured embedding model.
  - Upsert to Pinecone with deterministic IDs: `{file_hash}_{chunk_index}` where `file_hash` is SHA-256 of the relative file path truncated to 8 chars.
  - Return `IngestResult(files_processed: int, chunks_created: int, vectors_upserted: int)`.

- `DocumentIngester.ingest_file(path: str) -> IngestResult` — ingest a single Markdown file.
- Duplicate detection: before upserting, check if vectors with the same `source_file` already exist; if so, delete them first (re-index).

### Hybrid Retriever (`src/rag/retriever.py`)

- `HybridRetriever.__init__(index_name: str, embedding_model: str, documents: list[str], dense_weight: float = 0.7)`.
- `HybridRetriever.search(query: str, top_k: int = 10) -> list[RetrievalResult]`:
  1. Dense search: embed query → Pinecone query → get top `3 * top_k` results with scores.
  2. Sparse search: BM25 over the raw document chunks → get top `3 * top_k` results.
  3. Reciprocal Rank Fusion: for each document appearing in either list, compute `rrf_score = Σ 1/(k + rank)` where `k=60`, weighted by `dense_weight` for dense and `(1 - dense_weight)` for sparse.
  4. Return top `top_k` results sorted by RRF score.
- `RetrievalResult` fields: `text` (str), `metadata` (dict), `dense_score` (float | None), `sparse_score` (float | None), `rrf_score` (float).

### Reranker (`src/rag/reranker.py`)

- `Reranker.__init__(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2")`.
- `Reranker.rerank(query: str, results: list[RetrievalResult], top_k: int = 5) -> list[RetrievalResult]`:
  - Score each (query, result.text) pair with the cross-encoder.
  - Add `rerank_score` to each result.
  - Return top `top_k` sorted by `rerank_score` descending.

### LangGraph Pipeline (`src/rag/pipeline.py`)

- State type: `RAGState(TypedDict)` with fields: `question` (str), `retrieved` (list), `reranked` (list), `answer` (str), `sources` (list).
- Nodes:
  1. `retrieve` — call `HybridRetriever.search(question, top_k=20)`, store in `retrieved`.
  2. `rerank` — call `Reranker.rerank(question, retrieved, top_k=5)`, store in `reranked`.
  3. `generate` — format reranked chunks into RAG prompt, call LLM (`claude-sonnet-4-6`), store response in `answer`.
  4. `cite_sources` — parse the generated answer for `[1]`, `[2]` citation markers, map each to the corresponding reranked chunk's `source_file` and `section_heading`, store in `sources`.
- Edges: `START → retrieve → rerank → generate → cite_sources → END`.
- `RAGPipeline.query(question: str) -> RAGResponse` — invoke the graph, return `RAGResponse(answer: str, sources: list[SourceCitation])` where `SourceCitation` has `file`, `section`, `relevance_score`.

### Prompts (`src/rag/prompts.py`)

- System prompt: establishes the assistant as a technical documentation expert, instructs it to answer only from provided context, use citation markers `[1]`, `[2]`, etc., and say "I don't have enough information to answer this" when context is insufficient.
- User prompt template: includes numbered context chunks (format: `[{i}] (Source: {file} > {section})\n{text}`), then the user's question.

### Expected Functionality

- `ingester.ingest_directory("docs/api/")` on a directory with 10 Markdown files averaging 50 sections each → returns `IngestResult(files_processed=10, chunks_created=~500, vectors_upserted=~500)`.
- `pipeline.query("How do I authenticate with OAuth2?")` → answer cites specific documentation sections about OAuth2 with `[1]`, `[2]` markers mapped to source files.
- `pipeline.query("What is the meaning of life?")` → answer: "I don't have enough information to answer this" (off-topic question).
- `retriever.search("rate limiting", top_k=5)` → returns 5 results with RRF scores, including results from both dense and sparse retrievers.

## Acceptance Criteria

- Document ingestion preserves section heading hierarchy in chunk metadata and creates deterministic vector IDs.
- Re-ingesting a file deletes old vectors before upserting new ones.
- Hybrid retriever combines dense (Pinecone) and sparse (BM25) results using Reciprocal Rank Fusion with configurable weighting.
- Cross-encoder reranker reorders retrieved results and returns the top-k by relevance.
- The LangGraph pipeline chains retrieve → rerank → generate → cite_sources as a compiled state graph.
- Generated answers include numbered citation markers that map to specific source files and section headings.
- Off-topic questions receive a "not enough information" response instead of hallucinated answers.
