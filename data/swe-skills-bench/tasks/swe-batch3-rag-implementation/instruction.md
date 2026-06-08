# SWE-Skills-Bench: rag-implementation (batch3)

# Task: Implement a Hybrid RAG Retrieval Pipeline with Reranking for LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) is a framework for building LLM-powered applications. The project needs a Retrieval-Augmented Generation (RAG) pipeline that combines dense vector search with sparse keyword search (hybrid retrieval), performs multi-query expansion, applies reranking to the merged results, and tracks source citations. This should integrate with LangChain's retriever and document interfaces in the `libs/core` package.

## Files to Create/Modify

- `libs/core/langchain_core/retrievers/hybrid_retriever.py` (create) — Hybrid retriever combining dense and sparse search with reciprocal rank fusion
- `libs/core/langchain_core/retrievers/multi_query.py` (create) — Multi-query expansion that generates query variations and merges results
- `libs/core/langchain_core/retrievers/reranker.py` (create) — Cross-encoder reranking of merged retrieval results
- `libs/core/tests/unit_tests/retrievers/test_hybrid_retriever.py` (create) — Tests for hybrid retrieval and reranking pipeline

## Requirements

### Hybrid Retriever

- Implement a `HybridRetriever` that accepts two sub-retrievers: a `dense_retriever` (vector search) and a `sparse_retriever` (keyword search, e.g., BM25)
- Both sub-retrievers conform to LangChain's `BaseRetriever` interface
- Merge results using **Reciprocal Rank Fusion (RRF)**: score = Σ 1/(k + rank_i) across retrievers, where k is a constant (default: 60)
- Return the top `n` documents (configurable, default: 10) sorted by RRF score descending
- Deduplicate documents that appear in both retrievers' results using document `page_content` hash; the RRF score is the sum of scores from both sources

### Multi-Query Expansion

- Implement a `MultiQueryRetriever` that generates N query variations (default: 3) from the original query
- Query generation uses a configurable `query_generator` function: `(original_query) -> list[str]`
- Run each query variation through the underlying retriever (the `HybridRetriever` or any `BaseRetriever`)
- Merge all results using the same RRF fusion, deduplicating across queries
- Return the top `n` documents ranked by combined RRF score

### Reranking

- Implement a `Reranker` class that takes a list of documents and a query, and rescores them using a `scoring_function: (query, document) -> float`
- The `scoring_function` is injected (e.g., a cross-encoder model's predict function, or a simple keyword relevance scorer for testing)
- After rescoring, return documents sorted by score descending, with the score attached as `document.metadata["rerank_score"]`
- Support a `min_score` threshold (default: 0.0); documents scoring below this threshold are filtered out

### Citation Tracking

- Each document in the final output must include `metadata["source"]`, `metadata["retrieval_method"]` (one of `"dense"`, `"sparse"`, `"hybrid"`), and `metadata["rrf_score"]`
- Provide a `format_citations(documents) -> str` function that produces a numbered citation list: `[1] source_name (score: 0.85)\n[2] ...`

### Chunking Strategy

- Provide a `RecursiveChunker` class that splits text into chunks with configurable `chunk_size` (characters, default: 1000), `chunk_overlap` (characters, default: 200), and separators (default: `["\n\n", "\n", ". ", " "]`)
- The chunker attempts to split on the highest-priority separator that fits within `chunk_size`; if no separator fits, it falls back to character-level splitting
- Each chunk includes `metadata["chunk_index"]`, `metadata["start_char"]`, `metadata["end_char"]`

### Expected Functionality

- A hybrid retriever with dense returning [A, B, C] and sparse returning [B, D, E] produces a merged list where B has the highest RRF score (appearing in both)
- Multi-query with 3 variations and 10 results per query deduplicates and returns the top 10 across all 30 results
- Reranker with `min_score=0.5` filters out documents scoring below 0.5
- `format_citations` for 3 documents produces `"[1] doc1.pdf (score: 0.92)\n[2] doc2.pdf (score: 0.85)\n[3] doc3.pdf (score: 0.71)"`
- `RecursiveChunker` with chunk_size=100 and overlap=20 splits a 250-character text into 3 chunks with correct start/end character offsets

## Acceptance Criteria

- `HybridRetriever` correctly merges dense and sparse results using RRF with configurable k parameter
- Documents appearing in both retrievers receive summed RRF scores and are deduplicated
- `MultiQueryRetriever` generates query variations, retrieves for each, and merges with deduplication
- `Reranker` rescores and re-sorts documents, attaching `rerank_score` to metadata and filtering by `min_score`
- Citation metadata (`source`, `retrieval_method`, `rrf_score`) is present on all returned documents
- `format_citations` produces correctly numbered citation text
- `RecursiveChunker` respects chunk_size, overlap, separator priority, and includes correct chunk metadata
- Tests cover hybrid merging, deduplication, multi-query fusion, reranking thresholds, citation formatting, and chunking edge cases
