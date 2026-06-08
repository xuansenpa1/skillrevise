"""
Tests for the rag-implementation skill.
Validates a Document Q&A RAG pipeline for LangChain with chunking strategies,
hybrid search retrieval, pipeline orchestration, and evaluation metrics.
"""

import os
import re
import ast

REPO_DIR = "/workspace/langchain"
RAG_DIR = os.path.join(REPO_DIR, "libs", "langchain", "langchain", "rag")


class TestRagImplementation:
    """Tests for the LangChain RAG pipeline implementation."""

    # ── file_path_check ──────────────────────────────────────────────

    def test_pipeline_file_exists(self):
        """RAGPipeline module must exist."""
        path = os.path.join(RAG_DIR, "pipeline.py")
        assert os.path.isfile(path), f"Missing {path}"

    def test_chunker_file_exists(self):
        """DocumentChunker module must exist."""
        path = os.path.join(RAG_DIR, "chunker.py")
        assert os.path.isfile(path), f"Missing {path}"

    def test_retriever_file_exists(self):
        """HybridRetriever module must exist."""
        path = os.path.join(RAG_DIR, "retriever.py")
        assert os.path.isfile(path), f"Missing {path}"

    def test_evaluator_file_exists(self):
        """RetrievalEvaluator module must exist."""
        path = os.path.join(RAG_DIR, "evaluator.py")
        assert os.path.isfile(path), f"Missing {path}"

    # ── semantic_check ───────────────────────────────────────────────

    def _read(self, filename):
        path = os.path.join(RAG_DIR, filename)
        if not os.path.isfile(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_document_chunker_class(self):
        """DocumentChunker class must be defined with chunk and chunk_documents methods."""
        content = self._read("chunker.py")
        assert re.search(r"class\s+DocumentChunker", content), (
            "DocumentChunker class not defined"
        )
        assert re.search(r"def\s+chunk\b", content), "chunk method not defined"
        assert re.search(r"def\s+chunk_documents\b", content), "chunk_documents method not defined"

    def test_chunking_strategies(self):
        """DocumentChunker must support recursive, sentence, and sliding_window strategies."""
        content = self._read("chunker.py")
        for strategy in ["recursive", "sentence", "sliding_window"]:
            assert strategy in content, f"Strategy '{strategy}' not found in chunker.py"

    def test_hybrid_retriever_class(self):
        """HybridRetriever class must be defined with index and search methods."""
        content = self._read("retriever.py")
        assert re.search(r"class\s+HybridRetriever", content), (
            "HybridRetriever class not defined"
        )
        assert re.search(r"def\s+index\b", content), "index method not defined"
        assert re.search(r"def\s+search\b", content), "search method not defined"

    def test_reciprocal_rank_fusion(self):
        """HybridRetriever must implement Reciprocal Rank Fusion."""
        content = self._read("retriever.py")
        assert re.search(r"reciprocal|rrf|rank.*fusion|1/.*rank.*\+.*60", content, re.IGNORECASE), (
            "Reciprocal Rank Fusion not found in retriever"
        )

    def test_dense_and_sparse_search(self):
        """HybridRetriever must implement both dense and sparse search."""
        content = self._read("retriever.py")
        assert re.search(r"def\s+search_dense\b", content), "search_dense method not defined"
        assert re.search(r"def\s+search_sparse\b", content), "search_sparse method not defined"

    def test_bm25_in_sparse_search(self):
        """Sparse search must use BM25 or TF-IDF scoring."""
        content = self._read("retriever.py")
        assert re.search(r"bm25|tf.idf|tfidf|term.frequency|idf", content, re.IGNORECASE), (
            "BM25/TF-IDF scoring not found in sparse search"
        )

    def test_rag_pipeline_class(self):
        """RAGPipeline class must be defined with ingest and query methods."""
        content = self._read("pipeline.py")
        assert re.search(r"class\s+RAGPipeline", content), "RAGPipeline class not defined"
        assert re.search(r"def\s+ingest\b", content), "ingest method not defined"
        assert re.search(r"def\s+query\b", content), "query method not defined"

    def test_evaluator_metrics(self):
        """RetrievalEvaluator must define precision_at_k, recall_at_k, mrr, ndcg."""
        content = self._read("evaluator.py")
        assert re.search(r"class\s+RetrievalEvaluator", content), (
            "RetrievalEvaluator class not defined"
        )
        for metric in ["precision_at_k", "recall_at_k", "mrr", "ndcg"]:
            assert re.search(rf"def\s+{metric}\b", content), (
                f"{metric} method not defined in evaluator"
            )

    # ── functional_check ─────────────────────────────────────────────

    def test_all_files_valid_python(self):
        """All RAG module files must have valid syntax."""
        errors = []
        for fname in ["pipeline.py", "chunker.py", "retriever.py", "evaluator.py"]:
            content = self._read(fname)
            if not content:
                continue
            try:
                ast.parse(content)
            except SyntaxError as e:
                errors.append(f"{fname}: {e}")
        assert not errors, "Syntax errors:\n" + "\n".join(errors)

    def test_chunk_overlap_validation(self):
        """DocumentChunker must reject chunk_overlap >= chunk_size."""
        content = self._read("chunker.py")
        assert re.search(r"ValueError|overlap.*size|overlap.*>=|overlap.*chunk_size", content, re.IGNORECASE), (
            "chunk_overlap >= chunk_size validation not found"
        )

    def test_alpha_weighting_in_retriever(self):
        """HybridRetriever must use alpha parameter for dense/sparse weighting."""
        content = self._read("retriever.py")
        assert "alpha" in content, "alpha weighting parameter not found in retriever"

    def test_source_citations_in_pipeline(self):
        """Pipeline query must return sources for citation."""
        content = self._read("pipeline.py")
        assert re.search(r"sources|source|citation", content, re.IGNORECASE), (
            "Source citations not found in pipeline query response"
        )

    def test_no_info_fallback_message(self):
        """Pipeline must handle no-context case with appropriate message."""
        content = self._read("pipeline.py")
        assert re.search(
            r"don't have enough|no.*information|cannot answer|not.*enough",
            content, re.IGNORECASE
        ), "No-information fallback message not found in pipeline"

    def test_test_file_exists(self):
        """Test suite file must exist."""
        path = os.path.join(REPO_DIR, "tests", "test_rag_implementation.py")
        assert os.path.isfile(path), f"Missing {path}"
