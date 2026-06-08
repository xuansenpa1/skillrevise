"""
Tests for skill: rag-implementation
Repo: langchain-ai/langchain
Image: zhangyiiiiii/swe-skills-bench-python
Task: Build a RAG pipeline with hybrid search (dense + sparse + RRF),
      reranking, and evaluation metrics for LangChain.
"""

import ast
import os
import re
import subprocess

import pytest

REPO_DIR = "/workspace/langchain"
RAG_DIR = os.path.join(REPO_DIR, "libs", "langchain", "langchain", "rag")
TEST_DIR = os.path.join(REPO_DIR, "libs", "langchain", "tests", "unit_tests", "rag")

DOC_PROCESSOR_FILE = os.path.join(RAG_DIR, "document_processor.py")
RETRIEVER_FILE = os.path.join(RAG_DIR, "hybrid_retriever.py")
RERANKER_FILE = os.path.join(RAG_DIR, "reranker.py")
PIPELINE_FILE = os.path.join(RAG_DIR, "pipeline.py")
TEST_FILE = os.path.join(TEST_DIR, "test_rag_pipeline.py")


# ---------------------------------------------------------------------------
# Layer 1 — file_path_check
# ---------------------------------------------------------------------------

class TestFilePathCheck:
    """Verify all required RAG files were created."""

    def test_document_processor_exists(self):
        assert os.path.isfile(DOC_PROCESSOR_FILE), f"Expected {DOC_PROCESSOR_FILE}"

    def test_hybrid_retriever_exists(self):
        assert os.path.isfile(RETRIEVER_FILE), f"Expected {RETRIEVER_FILE}"

    def test_reranker_exists(self):
        assert os.path.isfile(RERANKER_FILE), f"Expected {RERANKER_FILE}"

    def test_pipeline_exists(self):
        assert os.path.isfile(PIPELINE_FILE), f"Expected {PIPELINE_FILE}"

    def test_test_file_exists(self):
        assert os.path.isfile(TEST_FILE), f"Expected {TEST_FILE}"


# ---------------------------------------------------------------------------
# Layer 2 — semantic_check
# ---------------------------------------------------------------------------

class TestSemanticDocumentProcessor:
    """Verify DocumentProcessor class."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        with open(DOC_PROCESSOR_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()
        self.tree = ast.parse(self.src)

    def test_class_defined(self):
        classes = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.ClassDef)]
        assert "DocumentProcessor" in classes, (
            f"Expected DocumentProcessor class; found: {classes}"
        )

    def test_chunk_method(self):
        funcs = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]
        assert "chunk" in funcs, "Expected chunk() method"

    def test_embed_method(self):
        funcs = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]
        assert "embed" in funcs, "Expected embed() method"

    def test_chunk_size_and_overlap_params(self):
        assert "chunk_size" in self.src, "Expected chunk_size parameter"
        assert "chunk_overlap" in self.src, "Expected chunk_overlap parameter"

    def test_overlap_validation(self):
        """chunk_overlap must be less than chunk_size."""
        has_validation = (
            "ValueError" in self.src
            and "overlap" in self.src
        )
        assert has_validation, (
            "Expected ValueError when chunk_overlap >= chunk_size"
        )

    def test_sentence_boundary_handling(self):
        """Chunking should respect sentence boundaries."""
        has_sentence = (
            "sentence" in self.src.lower()
            or ". " in self.src
            or "split" in self.src
            or "nltk" in self.src.lower()
        )
        assert has_sentence, (
            "Expected sentence boundary handling in chunk method"
        )


class TestSemanticHybridRetriever:
    """Verify HybridRetriever with RRF fusion."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        with open(RETRIEVER_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()
        self.tree = ast.parse(self.src)

    def test_class_defined(self):
        classes = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.ClassDef)]
        assert "HybridRetriever" in classes, (
            f"Expected HybridRetriever class; found: {classes}"
        )

    def test_search_method(self):
        funcs = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]
        assert "search" in funcs, "Expected search() method"

    def test_dense_scoring(self):
        """Must use cosine similarity for dense scoring."""
        assert "cosine" in self.src.lower() or "dot" in self.src.lower(), (
            "Expected cosine similarity for dense scoring"
        )

    def test_sparse_scoring_bm25(self):
        """Must use BM25 for sparse scoring."""
        assert "bm25" in self.src.lower() or "BM25" in self.src, (
            "Expected BM25 for sparse scoring"
        )

    def test_reciprocal_rank_fusion(self):
        """Must implement Reciprocal Rank Fusion."""
        has_rrf = (
            "rrf" in self.src.lower()
            or "reciprocal" in self.src.lower()
            or "1 / (k + rank" in self.src
            or "1/(k+" in self.src.replace(" ", "")
        )
        assert has_rrf, "Expected Reciprocal Rank Fusion implementation"

    def test_weight_validation(self):
        """dense_weight + sparse_weight must equal 1.0."""
        has_check = (
            "ValueError" in self.src
            and ("weight" in self.src)
        )
        assert has_check, (
            "Expected weight validation (sum to 1.0) with ValueError"
        )

    def test_rrf_k_constant(self):
        """RRF uses k=60 constant."""
        assert "60" in self.src, "Expected k=60 constant in RRF formula"


class TestSemanticReranker:
    """Verify Reranker class."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        with open(RERANKER_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()
        self.tree = ast.parse(self.src)

    def test_class_defined(self):
        classes = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.ClassDef)]
        assert "Reranker" in classes, (
            f"Expected Reranker class; found: {classes}"
        )

    def test_rerank_method(self):
        funcs = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]
        assert "rerank" in funcs, "Expected rerank() method"

    def test_min_score_filtering(self):
        assert "min_score" in self.src, "Expected min_score threshold parameter"

    def test_rerank_score_in_output(self):
        assert "rerank_score" in self.src, (
            "Expected rerank_score field in output documents"
        )


class TestSemanticPipeline:
    """Verify RAGPipeline class."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        with open(PIPELINE_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()
        self.tree = ast.parse(self.src)

    def test_class_defined(self):
        classes = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.ClassDef)]
        assert "RAGPipeline" in classes, (
            f"Expected RAGPipeline class; found: {classes}"
        )

    def test_ingest_method(self):
        funcs = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]
        assert "ingest" in funcs, "Expected ingest() method"

    def test_query_method(self):
        funcs = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]
        assert "query" in funcs, "Expected query() method"

    def test_evaluation_helpers(self):
        """Must have recall_at_k, mrr, ndcg_at_k evaluation functions."""
        # These may be in pipeline.py or a separate evaluation module
        all_src = self.src
        for candidate in [DOC_PROCESSOR_FILE, RETRIEVER_FILE]:
            if os.path.isfile(candidate):
                with open(candidate, "r", encoding="utf-8") as f:
                    all_src += f.read()
        # Also check for an evaluation module
        eval_path = os.path.join(RAG_DIR, "evaluation.py")
        if os.path.isfile(eval_path):
            with open(eval_path, "r", encoding="utf-8") as f:
                all_src += f.read()

        helpers = ["recall_at_k", "mrr", "ndcg"]
        found = [h for h in helpers if h in all_src]
        assert len(found) >= 2, (
            f"Expected at least 2 evaluation helpers (recall_at_k, mrr, ndcg_at_k); found: {found}"
        )


# ---------------------------------------------------------------------------
# Layer 3 — functional_check
# ---------------------------------------------------------------------------

class TestFunctionalRAG:
    """Functional checks — syntax and import validation."""

    def _parse(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            src = f.read()
        try:
            ast.parse(src)
            return True, None
        except SyntaxError as e:
            return False, str(e)

    def test_doc_processor_valid_python(self):
        ok, err = self._parse(DOC_PROCESSOR_FILE)
        assert ok, f"document_processor.py syntax error: {err}"

    def test_retriever_valid_python(self):
        ok, err = self._parse(RETRIEVER_FILE)
        assert ok, f"hybrid_retriever.py syntax error: {err}"

    def test_reranker_valid_python(self):
        ok, err = self._parse(RERANKER_FILE)
        assert ok, f"reranker.py syntax error: {err}"

    def test_pipeline_valid_python(self):
        ok, err = self._parse(PIPELINE_FILE)
        assert ok, f"pipeline.py syntax error: {err}"

    def test_test_file_valid_python(self):
        ok, err = self._parse(TEST_FILE)
        assert ok, f"test_rag_pipeline.py syntax error: {err}"

    def test_doc_processor_importable(self):
        """DocumentProcessor must be importable."""
        result = subprocess.run(
            f"python -c \"import sys; sys.path.insert(0, '{os.path.dirname(RAG_DIR)}'); "
            f"from rag.document_processor import DocumentProcessor; print('OK')\"",
            shell=True, capture_output=True, text=True, timeout=30,
            cwd=REPO_DIR,
        )
        if result.returncode != 0:
            result2 = subprocess.run(
                f"python -c \"import sys; sys.path.insert(0, '{RAG_DIR}'); "
                f"from document_processor import DocumentProcessor; print('OK')\"",
                shell=True, capture_output=True, text=True, timeout=30,
                cwd=REPO_DIR,
            )
            assert "OK" in result.stdout or "OK" in result2.stdout, (
                f"Could not import DocumentProcessor:\n{result.stderr[:300]}\n{result2.stderr[:300]}"
            )

    def test_pipeline_returns_answer_and_sources(self):
        """RAGPipeline.query return must include answer and sources keys."""
        with open(PIPELINE_FILE, "r", encoding="utf-8") as f:
            src = f.read()
        for key in ["answer", "sources"]:
            assert key in src, (
                f"Expected '{key}' key in RAGPipeline.query return dict"
            )
