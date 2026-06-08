# SWE-Skills-Bench: rag-implementation (batch5)

# Task: Build a RAG Pipeline with Hybrid Retrieval for LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) provides composable components for building retrieval-augmented generation (RAG) pipelines. This task requires implementing a complete RAG pipeline that loads documents, chunks them, creates embeddings, stores vectors in a FAISS index, and performs hybrid retrieval (combining dense vector search with BM25 sparse search) to answer questions. The pipeline should be implemented as a reusable module within the LangChain community integrations.

## Files to Create/Modify

- `libs/community/langchain_community/rag/document_processor.py` (create) — Document loading and chunking pipeline: reads Markdown files, splits them using `RecursiveCharacterTextSplitter` with configurable chunk size and overlap, and attaches source metadata to each chunk.
- `libs/community/langchain_community/rag/hybrid_retriever.py` (create) — Hybrid retriever combining FAISS dense vector search and BM25 sparse search with reciprocal rank fusion (RRF) to merge results.
- `libs/community/langchain_community/rag/qa_chain.py` (create) — QA chain that takes a question, retrieves context via the hybrid retriever, and formats a prompt for the LLM with the retrieved context and question.
- `libs/community/langchain_community/rag/__init__.py` (create) — Package init exposing `DocumentProcessor`, `HybridRetriever`, and `QAChain`.
- `libs/community/tests/unit_tests/rag/test_rag_pipeline.py` (create) — Tests for document processing, retrieval ranking, and QA chain formatting.

## Requirements

### Document Processor

- `DocumentProcessor(chunk_size=512, chunk_overlap=64)` — configurable chunking parameters.
- `load_directory(path)` — recursively loads all `.md` files from the given directory path. Each document's metadata includes `source` (file path) and `chunk_index`.
- `process(documents)` — splits documents into chunks and returns a list of `Document` objects with text content and metadata.
- Chunks that would be shorter than 50 characters after stripping whitespace are discarded.

### Hybrid Retriever

- `HybridRetriever(embeddings, faiss_index, bm25_corpus, k=5, dense_weight=0.6, sparse_weight=0.4)`.
- `dense_search(query, k)` — embeds the query and searches the FAISS index, returning top-k results with scores.
- `sparse_search(query, k)` — uses BM25 scoring over the tokenized corpus, returning top-k results with scores.
- `retrieve(query, k=5)` — performs both searches, merges results using Reciprocal Rank Fusion: `RRF_score = Σ 1/(rank + 60)` for each document across both result lists. Returns top-k unique documents sorted by RRF score descending.
- Documents appearing in only one result list still receive their single RRF contribution.

### QA Chain

- `QAChain(retriever, prompt_template=None)` — accepts a retriever and optional custom prompt template.
- Default prompt template: `"Answer the question based on the following context.\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:"`.
- `build_prompt(question)` — retrieves context, concatenates document texts with `\n---\n` separators, and formats the prompt.
- `build_prompt` returns a dict with `prompt` (formatted string), `source_documents` (list of retrieved docs), and `retrieval_scores` (list of RRF scores).

### Expected Functionality

- Processing 10 Markdown files totaling 50KB with `chunk_size=512` → produces ~100 chunks, each with metadata.
- `HybridRetriever.retrieve("How to configure logging?")` → returns 5 documents ranked by RRF fusion, with the most relevant document appearing first regardless of whether it ranked highest in dense or sparse search alone.
- `QAChain.build_prompt("What is the retry policy?")` → returns a formatted prompt string with 5 context passages separated by `---` and the question appended.

## Acceptance Criteria

- `DocumentProcessor` loads Markdown files, splits them into chunks respecting size/overlap settings, and discards short chunks.
- `HybridRetriever` correctly implements both dense (FAISS) and sparse (BM25) search and merges with RRF.
- The RRF merge handles documents appearing in only one result list.
- `QAChain.build_prompt` returns a complete prompt with context and source document references.
- Tests verify chunking behavior, RRF score computation with known rankings, and prompt formatting.
