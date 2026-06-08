# SWE-Skills-Bench: rag-implementation (batch4)

# Task: Build a Retrieval-Augmented Generation Pipeline with Hybrid Search for LangChain

## Background

The LangChain repository (https://github.com/langchain-ai/langchain) provides building blocks for LLM-powered applications. A new RAG module is needed that ingests a corpus of documents, chunks and embeds them, stores them in a vector store, and retrieves relevant passages using hybrid search (combining dense semantic retrieval with sparse keyword matching via Reciprocal Rank Fusion). The pipeline must support reranking retrieved results, formatting context for the LLM, and evaluating retrieval quality with standard metrics.

## Files to Create/Modify

- `libs/langchain/langchain/rag/document_processor.py` (create) — Document chunking and embedding pipeline with configurable chunk size/overlap
- `libs/langchain/langchain/rag/hybrid_retriever.py` (create) — Hybrid retriever combining dense and sparse retrieval with Reciprocal Rank Fusion
- `libs/langchain/langchain/rag/reranker.py` (create) — Cross-encoder reranking module with score-based filtering
- `libs/langchain/langchain/rag/pipeline.py` (create) — End-to-end RAG pipeline orchestrating ingestion, retrieval, reranking, and generation
- `libs/langchain/tests/unit_tests/rag/test_rag_pipeline.py` (create) — Tests for chunking, retrieval, reranking, and pipeline integration

## Requirements

### Document Processor

- `DocumentProcessor` class accepting: `chunk_size` (int, default 500), `chunk_overlap` (int, default 100), `embedding_function` (callable: str → list[float])
- `chunk(text: str, metadata: dict) -> list[dict]` — splits text into overlapping chunks; each chunk dict contains `"text"`, `"metadata"` (inheriting from source), `"chunk_index"` (int)
- Chunk boundaries must respect sentence endings when possible — do not split mid-sentence if the sentence boundary falls within the overlap window
- `chunk_overlap` must be less than `chunk_size`; otherwise raise `ValueError`
- `embed(chunks: list[dict]) -> list[dict]` — adds an `"embedding"` field (list of floats) to each chunk dict

### Hybrid Retriever

- `HybridRetriever` class accepting: `documents` (list of chunk dicts with embeddings), `dense_weight` (float, default 0.7), `sparse_weight` (float, default 0.3)
- `search(query: str, query_embedding: list[float], top_k: int = 5) -> list[dict]` — returns the top-k documents by fused score
- Dense scoring: cosine similarity between `query_embedding` and each document's `"embedding"`
- Sparse scoring: BM25 score between `query` text and each document's `"text"`
- Fusion: Reciprocal Rank Fusion (RRF) — for each document, `rrf_score = Σ 1 / (k + rank_i)` where `k = 60` and `rank_i` is the document's rank in each retrieval list; final score = `dense_weight * rrf_dense + sparse_weight * rrf_sparse`
- `dense_weight + sparse_weight` must equal 1.0; otherwise raise `ValueError`

### Reranker

- `Reranker` class accepting: `score_function` (callable: (query, text) → float), `min_score` (float, optional threshold)
- `rerank(query: str, documents: list[dict], top_k: int = 3) -> list[dict]` — scores each document using `score_function`, filters by `min_score` if set, sorts by descending score, returns top_k
- Each returned document dict must include the original fields plus `"rerank_score"` (float)

### RAG Pipeline

- `RAGPipeline` class accepting: `processor` (DocumentProcessor), `retriever_class` (HybridRetriever class), `reranker` (Reranker, optional), `generate_fn` (callable: (query, context_docs) → str)
- `ingest(texts: list[str], metadatas: list[dict])` — chunks, embeds, and stores all documents; builds the retriever
- `query(question: str, top_k: int = 5, rerank_top_k: int = 3) -> dict` — retrieves, optionally reranks, generates an answer; returns `{"answer": str, "sources": list[dict], "retrieval_scores": list[float]}`
- Each source dict must include `"text"`, `"metadata"`, and `"score"`

### Evaluation Helpers

- `recall_at_k(retrieved_ids: list, relevant_ids: list, k: int) -> float` — fraction of relevant documents found in the top-k retrieved
- `mrr(retrieved_ids: list, relevant_ids: list) -> float` — Mean Reciprocal Rank: 1 / rank of the first relevant result (0 if none found)
- `ndcg_at_k(retrieved_ids: list, relevant_ids: list, k: int) -> float` — Normalized Discounted Cumulative Gain

### Expected Functionality

- Ingesting 3 documents of ~1000 words each with chunk_size=500 produces approximately 6–8 chunks per document
- Querying "What are the main features?" returns documents ranked by fused dense+sparse score with the most relevant chunk first
- Reranking re-orders results by cross-encoder score and filters out documents below `min_score`
- `recall_at_k([1,3,5,7], [1,5,9], k=4)` returns approximately 0.667 (2 of 3 relevant found)
- `mrr([3,1,5], [5])` returns 1/3 (relevant doc at rank 3)

## Acceptance Criteria

- Document processor splits text into overlapping chunks respecting sentence boundaries and embeds them
- Hybrid retriever correctly combines dense cosine similarity and sparse BM25 using Reciprocal Rank Fusion
- Reranker re-scores and filters documents by minimum score threshold
- RAG pipeline orchestrates ingestion, retrieval, reranking, and generation end-to-end
- Evaluation helpers compute recall@k, MRR, and NDCG@k correctly
- Invalid configurations (overlap ≥ chunk_size, weights not summing to 1.0) raise `ValueError`
- All tests pass covering chunking, retrieval scoring, reranking, pipeline integration, and evaluation metrics
