# SWE-Skills-Bench: rag-implementation (batch7)

# Task: Implement a Modular RAG Pipeline with Hybrid Retrieval in LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) provides building blocks for LLM applications. The task is to implement a production-grade Retrieval-Augmented Generation (RAG) pipeline that supports hybrid retrieval (combining dense vector search with sparse BM25 search), reciprocal rank fusion for merging results, configurable document chunking, and answer generation with source attribution.

## Files to Create/Modify

- `libs/langchain/langchain/retrievers/hybrid_retriever.py` (create) — `HybridRetriever` that combines dense and sparse retrieval with reciprocal rank fusion
- `libs/langchain/langchain/text_splitter/semantic_chunker.py` (create) — `SemanticChunker` that splits documents at semantic boundaries using embedding similarity
- `libs/langchain/langchain/chains/rag_chain.py` (create) — `RAGChain` that orchestrates retrieval, context assembly, and answer generation with source citations
- `libs/langchain/tests/unit_tests/retrievers/test_hybrid_retriever.py` (create) — Unit tests for hybrid retrieval
- `libs/langchain/tests/unit_tests/chains/test_rag_chain.py` (create) — Unit tests for the RAG chain

## Requirements

### `HybridRetriever` (`hybrid_retriever.py`)

Inherits from `langchain_core.retrievers.BaseRetriever`.

#### Constructor
```python
HybridRetriever(
    dense_retriever: BaseRetriever,
    sparse_retriever: BaseRetriever,
    k: int = 10,
    dense_weight: float = 0.6,
    sparse_weight: float = 0.4,
    fusion_method: str = "rrf"    # "rrf" or "weighted_score"
)
```

#### `_get_relevant_documents(query: str) -> list[Document]`
1. Query both `dense_retriever` and `sparse_retriever` with the same query, requesting `k * 2` results from each
2. If `fusion_method == "rrf"` (Reciprocal Rank Fusion):
   - For each document, compute: $score = \sum_{r \in retrievers} \frac{weight_r}{k_{rrf} + rank_r}$ where $k_{rrf} = 60$ and $rank_r$ is the 1-based position in that retriever's results
   - Deduplicate documents by `page_content` hash — if the same document appears in both retrievers, sum their scores
3. If `fusion_method == "weighted_score"`:
   - Normalize scores from each retriever to [0, 1]
   - Compute weighted sum: `dense_weight * dense_score + sparse_weight * sparse_score`
   - Deduplicate by content hash with score summation
4. Sort by descending score, return top `k` documents
5. Attach the fusion score as `metadata["retrieval_score"]` on each returned document

### `SemanticChunker` (`semantic_chunker.py`)

#### Constructor
```python
SemanticChunker(
    embedding_function: Callable[[str], list[float]],
    max_chunk_size: int = 1000,       # Maximum characters per chunk
    min_chunk_size: int = 100,        # Minimum characters per chunk
    similarity_threshold: float = 0.5, # Cosine similarity threshold for splitting
    overlap_sentences: int = 1         # Number of overlapping sentences between chunks
)
```

#### `split_text(text: str) -> list[str]`
1. Split the text into sentences (using regex: split on `.!?` followed by whitespace)
2. Compute embeddings for each sentence
3. Compute cosine similarity between consecutive sentence embeddings
4. Identify split points where similarity between consecutive sentences drops below `similarity_threshold`
5. Group sentences into chunks, respecting `max_chunk_size` (force a split if a chunk exceeds max size even without a similarity drop)
6. Merge chunks smaller than `min_chunk_size` with the previous chunk
7. Add `overlap_sentences` sentences from the end of the previous chunk to the beginning of the next chunk
8. Return the list of chunk strings

#### `split_documents(documents: list[Document]) -> list[Document]`
- Apply `split_text` to each document's `page_content`
- Preserve the original document's metadata on each chunk, adding `chunk_index` (0-based) to metadata

### `RAGChain` (`rag_chain.py`)

#### Constructor
```python
RAGChain(
    retriever: BaseRetriever,
    llm: BaseLLM,
    system_prompt: str = "Answer the question based on the provided context. Cite sources using [1], [2] notation.",
    max_context_tokens: int = 3000,
    return_sources: bool = True
)
```

#### `invoke(query: str) -> RAGResponse`
1. Retrieve documents using the configured retriever
2. Assemble context: number each document `[1]`, `[2]`, etc., concatenate their `page_content` up to `max_context_tokens` estimated by character count ÷ 4
3. Construct the prompt: system prompt + context block + user query
4. Call the LLM with the constructed prompt
5. Return a `RAGResponse` dataclass:
   ```python
   @dataclass
   class RAGResponse:
       answer: str                    # LLM-generated answer
       sources: list[Document]        # Retrieved documents used in context
       query: str                     # Original query
       context_length: int            # Number of characters in the context block
   ```

#### `invoke_with_streaming(query: str) -> Iterator[str]`
- Same as `invoke` but uses the LLM's streaming interface to yield answer tokens incrementally

## Expected Functionality

- Given a dense retriever returning documents A, B, C (ranked) and a sparse retriever returning B, D, A (ranked):
  - RRF fusion: B gets the highest score (appears in both), followed by A, then C and D
  - The top-k results are deduped and sorted by fused score
- `SemanticChunker` with threshold 0.5 splits a document at topic boundaries where consecutive sentence similarity drops below 0.5
- `RAGChain.invoke("What is X?")` retrieves relevant documents, assembles numbered context, calls the LLM, and returns an answer with source references

## Acceptance Criteria

- `HybridRetriever` correctly implements reciprocal rank fusion with configurable weights
- Documents appearing in both retrievers have their RRF scores summed (not duplicated in results)
- `SemanticChunker` splits text at semantic boundaries and respects max/min chunk size constraints
- Sentence overlap between consecutive chunks equals `overlap_sentences`
- `RAGChain` truncates context to `max_context_tokens` and numbers source documents sequentially
- `RAGResponse` includes the retrieved source documents and the original query
- `invoke_with_streaming` yields answer tokens incrementally
- All classes follow LangChain's base class interfaces and are properly typed
