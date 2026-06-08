# SWE-Skills-Bench: rag-implementation (batch8)

# Task: Build a Document Q&A RAG Pipeline for LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) is a framework for building LLM applications. The project needs a complete Retrieval-Augmented Generation (RAG) pipeline that ingests documents, chunks them with configurable strategies, builds a vector store with an in-memory FAISS index, retrieves relevant context for queries, and generates grounded answers with source citations. The pipeline must support hybrid search (combining semantic and keyword matching) and include retrieval quality evaluation metrics.

## Files to Create/Modify

- `libs/langchain/langchain/rag/pipeline.py` (create) — `RAGPipeline` class orchestrating document ingestion, retrieval, and answer generation with configurable chunking, embedding, and retrieval strategies
- `libs/langchain/langchain/rag/chunker.py` (create) — `DocumentChunker` class implementing recursive character splitting, sentence-based splitting, and sliding window chunking with configurable overlap
- `libs/langchain/langchain/rag/retriever.py` (create) — `HybridRetriever` class combining dense vector search (cosine similarity) with sparse keyword search (BM25) using weighted reciprocal rank fusion
- `libs/langchain/langchain/rag/evaluator.py` (create) — `RetrievalEvaluator` class computing retrieval quality metrics: precision@k, recall@k, MRR, and NDCG
- `tests/test_rag_implementation.py` (create) — Tests covering chunking strategies, retrieval accuracy, hybrid search fusion, and evaluation metrics

## Requirements

### DocumentChunker

- Constructor: `DocumentChunker(strategy: str = "recursive", chunk_size: int = 512, chunk_overlap: int = 50)`
- Strategies:
  - `"recursive"`: Split by `\n\n`, then `\n`, then `. `, then ` `, then character-level, targeting `chunk_size` tokens with `chunk_overlap` token overlap between consecutive chunks
  - `"sentence"`: Split on sentence boundaries (`. `, `! `, `? `, plus newlines), then group sentences until `chunk_size` is reached
  - `"sliding_window"`: Fixed-size windows of `chunk_size` tokens with `chunk_overlap` overlap
- `chunk(text: str) -> list[dict]` — Return list of `{"content": str, "metadata": {"chunk_index": int, "start_char": int, "end_char": int}}`
- `chunk_documents(documents: list[dict]) -> list[dict]` — Each input document has `{"content": str, "metadata": dict}`; chunk each document and propagate the source metadata (e.g., `source_file`, `page_number`) into each chunk's metadata
- Raise `ValueError` if `chunk_overlap >= chunk_size`
- Token counting: approximate as `len(text.split())`

### HybridRetriever

- Constructor: `HybridRetriever(embedding_fn: Callable[[str], list[float]], alpha: float = 0.7)` where `alpha` is the weight for dense search (1-alpha for sparse)
- `index(chunks: list[dict]) -> None` — Build both a dense index (store embeddings in a numpy array for cosine similarity search) and a sparse index (compute BM25 term frequencies using TF-IDF with vocabulary built from all chunks)
- `search(query: str, top_k: int = 5) -> list[dict]` — Perform dense search and sparse search independently, each returning top `top_k * 2` candidates, then fuse using Reciprocal Rank Fusion: `score(d) = alpha * 1/(rank_dense + 60) + (1-alpha) * 1/(rank_sparse + 60)`, return top `top_k` by fused score
- Each result must include `{"content": str, "metadata": dict, "score": float, "dense_rank": int, "sparse_rank": int}`
- `search_dense(query: str, top_k: int) -> list[dict]` — Dense-only search using cosine similarity
- `search_sparse(query: str, top_k: int) -> list[dict]` — Sparse-only search using BM25 scoring
- If no chunks have been indexed, `search()` must return an empty list

### RAGPipeline

- Constructor: `RAGPipeline(chunker: DocumentChunker, retriever: HybridRetriever, llm_fn: Callable[[str], str], system_prompt: str = None)`
- `ingest(documents: list[dict]) -> int` — Chunk all documents and index them in the retriever; return the number of chunks created
- `query(question: str, top_k: int = 5) -> dict` — Retrieve top_k chunks, format them as context, build a prompt with the system prompt + context + question, call `llm_fn`, and return `{"answer": str, "sources": list[dict], "context_used": str}`
- The prompt format for LLM calls: `"{system_prompt}\n\nContext:\n{formatted_chunks}\n\nQuestion: {question}\n\nAnswer based only on the context above. If the context does not contain the answer, say 'I don't have enough information to answer this question.' Cite sources by chunk index."`
- `sources` must be the list of retrieved chunks with their metadata, so the answer can be traced back to specific document sections

### RetrievalEvaluator

- Constructor: `RetrievalEvaluator()`
- `precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float` — Proportion of retrieved items in top k that are in the relevant set
- `recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float` — Proportion of relevant items found in top k
- `mrr(retrieved: list[str], relevant: set[str]) -> float` — Reciprocal of the rank of the first relevant item (0.0 if none found)
- `ndcg(retrieved: list[str], relevant: set[str], k: int) -> float` — Normalized Discounted Cumulative Gain at k, using binary relevance (1 if in relevant set, 0 otherwise)
- `evaluate_retriever(test_queries: list[dict], retriever: HybridRetriever, k: int = 5) -> dict` — Each test query has `{"query": str, "relevant_chunk_ids": list[str]}`; return aggregated metrics across all queries

### Edge Cases

- Empty documents list: `ingest()` returns 0 and `search()` returns empty list
- Query with no relevant chunks in the index: pipeline returns the "I don't have enough information" answer with empty sources
- Chunks with identical content: must be stored and retrieved as separate entries (no deduplication)
- BM25 sparse search with query terms not in vocabulary: return score of 0 for all documents

## Expected Functionality

- Ingesting 10 documents of ~1000 words each with `chunk_size=200` produces ~50 chunks stored in the retriever
- Querying "What is the return policy?" retrieves chunks containing return policy information from the relevant source document
- Hybrid search with `alpha=0.7` ranks a chunk that is both semantically similar and keyword-matching higher than a chunk that only matches on one dimension
- `RetrievalEvaluator` reports precision@5, recall@5, MRR, and NDCG for a set of labelled test queries
- A query about a topic not covered in any document returns "I don't have enough information" with empty sources

## Acceptance Criteria

- `DocumentChunker` produces chunks respecting the configured size and overlap for all three strategies
- `HybridRetriever` combines dense and sparse search using reciprocal rank fusion with configurable alpha weighting
- `RAGPipeline.query()` returns an answer, source chunks, and the context string used for generation
- `RetrievalEvaluator` computes precision@k, recall@k, MRR, and NDCG matching standard IR metric definitions
- Empty inputs, missing vocabulary terms, and no-match queries are handled gracefully
- All tests pass with `pytest`
