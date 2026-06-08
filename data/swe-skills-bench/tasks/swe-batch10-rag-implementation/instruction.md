# SWE-Skills-Bench: rag-implementation (batch10)

# Task: Implement Hybrid RAG Pipeline with Reranking for LangChain

## Background

LangChain's `libs/community/` package needs a production-grade RAG retriever that combines dense vector search with sparse BM25 keyword matching, applies cross-encoder reranking, and supports parent-document retrieval for preserving context windows. The implementation must integrate with LangChain's existing retriever abstractions in `libs/core/` and provide a LangGraph-based orchestration graph that chains retrieval, reranking, and generation steps.

## Files to Create/Modify

- `libs/community/langchain_community/retrievers/hybrid_rerank_retriever.py` (new) — Hybrid retriever combining dense+sparse search with cross-encoder reranking, extending `BaseRetriever`
- `libs/community/langchain_community/retrievers/parent_chunk_retriever.py` (new) — Parent-document retriever that indexes small chunks but returns enclosing parent documents for full context
- `libs/community/langchain_community/graphs/rag_pipeline.py` (new) — LangGraph `StateGraph` wiring retrieval, optional reranking, contextual compression, and generation into a single compiled graph
- `libs/community/langchain_community/utils/chunking.py` (new) — Chunking utilities providing recursive character splitting, token-based splitting, and markdown-header-aware splitting with configurable overlap
- `libs/community/tests/unit_tests/retrievers/test_hybrid_rerank_retriever.py` (new) — Unit tests for hybrid retriever
- `libs/community/tests/unit_tests/retrievers/test_parent_chunk_retriever.py` (new) — Unit tests for parent-chunk retriever
- `libs/community/tests/unit_tests/graphs/test_rag_pipeline.py` (new) — Unit tests for the RAG pipeline graph

## Requirements

### HybridRerankRetriever

- Subclass `langchain_core.retrievers.BaseRetriever`
- Accept a dense retriever (any `BaseRetriever`), a sparse retriever (BM25-based), and a list of weight floats for Reciprocal Rank Fusion (RRF)
- Implement `_get_relevant_documents(query: str) -> list[Document]` that:
  1. Queries both dense and sparse retrievers
  2. Fuses ranked lists using RRF with the formula `score = Σ 1/(k + rank)` where `k` is a configurable constant (default 60)
  3. Optionally reranks the fused top-N results using a cross-encoder model name passed at init
  4. Returns the final top-k documents with `metadata["retrieval_score"]` set on each
- Accept `dense_weight` and `sparse_weight` floats (must sum to 1.0); raise `ValueError` if they don't
- Accept `rerank_top_n: int` controlling how many candidates are sent to the reranker (default 50)
- If no reranker model is provided, skip reranking and return RRF-fused results directly

### ParentChunkRetriever

- Accept a vector store instance, a `child_chunk_size: int` (default 400), a `parent_chunk_size: int` (default 2000), and `chunk_overlap: int` (default 100)
- On `add_documents(docs: list[Document])`:
  - Split each doc into parent chunks, then each parent into child chunks
  - Embed and index child chunks in the vector store with `metadata["parent_id"]`
  - Store parent chunks keyed by UUID in an in-memory `dict`
- On `_get_relevant_documents(query)`:
  - Retrieve top-k child chunks via similarity search
  - Map each child back to its parent via `parent_id`
  - Deduplicate parents, preserving order of first occurrence
  - Return parent documents
- Raise `ValueError` if `child_chunk_size >= parent_chunk_size`

### RAG Pipeline Graph

- Define a `RAGState` TypedDict with keys: `question: str`, `context: list[Document]`, `answer: str`, `sources: list[str]`
- Build a `StateGraph` with nodes: `retrieve`, `rerank` (conditional), `compress`, `generate`
- The `retrieve` node invokes the retriever and populates `context`
- The `rerank` node is skipped if the retriever already applies reranking (check a `reranking_applied` flag in state)
- The `compress` node uses LLM-based extraction to trim retrieved documents to only query-relevant passages
- The `generate` node formats a prompt with context and question, calls the LLM, and populates `answer` and `sources` (extracted citation IDs from document metadata)
- Expose a `build_rag_graph(retriever, llm, enable_reranking: bool, enable_compression: bool) -> CompiledGraph` factory function

### Chunking Utilities

- `recursive_split(text: str, chunk_size: int, chunk_overlap: int, separators: list[str] | None) -> list[str]` — split text trying each separator in order, falling back to character split
- `token_split(text: str, chunk_size: int, chunk_overlap: int, encoding: str) -> list[str]` — split by token count using tiktoken encoding name (e.g. `"cl100k_base"`)
- `markdown_split(text: str, headers: list[tuple[str, str]]) -> list[Document]` — split on markdown headers, attaching header hierarchy as metadata
- Raise `ValueError` if `chunk_overlap >= chunk_size`
- Raise `ValueError` if `chunk_size <= 0`

### Expected Functionality

- Hybrid retrieval with `dense_weight=0.7, sparse_weight=0.3` on a corpus where the query term appears verbatim in one doc but is semantically related to another → both documents appear in results, RRF score combines both signals
- Hybrid retriever with `dense_weight=0.5, sparse_weight=0.6` → raises `ValueError` (sum > 1.0)
- Hybrid retriever with `rerank_model=None` → returns RRF-fused results without calling any cross-encoder
- Parent-chunk retriever with `child_chunk_size=400, parent_chunk_size=2000` on a 5000-char document → child hits map back to 2–3 parent chunks; returned documents are each ~2000 chars
- Parent-chunk retriever with `child_chunk_size=2000, parent_chunk_size=400` → raises `ValueError`
- RAG graph with compression disabled → skips compress node, passes raw retrieved docs to generate
- RAG graph generate node given empty context → answer contains "I don't have enough information" or equivalent
- `recursive_split("short", chunk_size=1000, chunk_overlap=100)` → returns `["short"]` (no split needed)
- `token_split(text, chunk_size=512, chunk_overlap=50, encoding="cl100k_base")` → each chunk has at most 512 tokens
- `markdown_split(text)` on a doc with `## Intro` followed by `### Details` → returns documents with metadata `{"Header 2": "Intro", "Header 3": "Details"}`
- `recursive_split(text, chunk_size=100, chunk_overlap=200)` → raises `ValueError`

## Acceptance Criteria

- `python -m pytest libs/community/tests/unit_tests/retrievers/test_hybrid_rerank_retriever.py -v` passes
- `python -m pytest libs/community/tests/unit_tests/retrievers/test_parent_chunk_retriever.py -v` passes
- `python -m pytest libs/community/tests/unit_tests/graphs/test_rag_pipeline.py -v` passes
- RRF fusion produces different rankings than either dense or sparse alone when scores diverge
- Reranker reorders the initial RRF results (verified with a mock cross-encoder returning known scores)
- Parent-chunk retriever returns parent-sized documents, not child-sized fragments
- RAG graph compiles and is invocable with a question string, returning an answer and source list
- All chunking functions reject invalid parameters with `ValueError` before processing
- No direct imports from `langchain_community` inside `libs/core/`
