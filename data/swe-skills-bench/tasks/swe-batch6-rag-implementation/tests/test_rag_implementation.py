"""
Test skill: rag-implementation
Verify that the Agent builds a RAG system with document ingestion,
hybrid retrieval (dense + BM25 + RRF), cross-encoder reranking,
LangGraph pipeline, and citation tracking.
"""

import os
import re
import ast
import subprocess
import pytest


class TestRagImplementation:
    REPO_DIR = "/workspace/langchain"

    # === File Path Checks ===

    def test_ingestion_file_exists(self):
        path = os.path.join(self.REPO_DIR, "src/rag/ingestion.py")
        assert os.path.exists(path), f"ingestion.py not found at {path}"

    def test_retriever_file_exists(self):
        path = os.path.join(self.REPO_DIR, "src/rag/retriever.py")
        assert os.path.exists(path), f"retriever.py not found at {path}"

    def test_reranker_file_exists(self):
        path = os.path.join(self.REPO_DIR, "src/rag/reranker.py")
        assert os.path.exists(path), f"reranker.py not found at {path}"

    def test_pipeline_file_exists(self):
        path = os.path.join(self.REPO_DIR, "src/rag/pipeline.py")
        assert os.path.exists(path), f"pipeline.py not found at {path}"

    def test_prompts_file_exists(self):
        path = os.path.join(self.REPO_DIR, "src/rag/prompts.py")
        assert os.path.exists(path), f"prompts.py not found at {path}"

    def test_init_file_exists(self):
        path = os.path.join(self.REPO_DIR, "src/rag/__init__.py")
        assert os.path.exists(path), f"__init__.py not found at {path}"

    # === Semantic Checks ===

    def test_ingestion_class_defined(self):
        """Verify DocumentIngester class with ingest methods"""
        path = os.path.join(self.REPO_DIR, "src/rag/ingestion.py")
        with open(path, "r") as f:
            content = f.read()

        assert "DocumentIngester" in content, "Must define DocumentIngester class"
        assert re.search(r"def\s+ingest_directory", content), "Missing ingest_directory"
        assert re.search(r"def\s+ingest_file", content), "Missing ingest_file"

    def test_ingestion_uses_recursive_splitter(self):
        """Verify ingestion uses RecursiveCharacterTextSplitter"""
        path = os.path.join(self.REPO_DIR, "src/rag/ingestion.py")
        with open(path, "r") as f:
            content = f.read()

        assert "RecursiveCharacterTextSplitter" in content or "TextSplitter" in content, (
            "Should use RecursiveCharacterTextSplitter for chunking"
        )
        assert "1000" in content, "chunk_size should be 1000"
        assert "200" in content, "chunk_overlap should be 200"

    def test_ingestion_preserves_heading_metadata(self):
        """Verify chunks include section heading and hierarchy metadata"""
        path = os.path.join(self.REPO_DIR, "src/rag/ingestion.py")
        with open(path, "r") as f:
            content = f.read()

        assert "section_heading" in content or "heading" in content, (
            "Chunk metadata should include section_heading"
        )
        assert "heading_hierarchy" in content or "hierarchy" in content, (
            "Chunk metadata should include heading hierarchy"
        )

    def test_ingestion_uses_deterministic_ids(self):
        """Verify vector IDs use SHA-256 hash of file path"""
        path = os.path.join(self.REPO_DIR, "src/rag/ingestion.py")
        with open(path, "r") as f:
            content = f.read()

        assert "sha256" in content.lower() or "hashlib" in content, (
            "Vector IDs should use SHA-256 hash for deterministic IDs"
        )

    def test_retriever_implements_hybrid_search(self):
        """Verify HybridRetriever combines dense + BM25 + RRF"""
        path = os.path.join(self.REPO_DIR, "src/rag/retriever.py")
        with open(path, "r") as f:
            content = f.read()

        assert "HybridRetriever" in content, "Must define HybridRetriever class"
        assert "BM25" in content or "bm25" in content, "Should use BM25 for sparse search"
        assert "rrf" in content.lower() or "reciprocal" in content.lower(), (
            "Should use Reciprocal Rank Fusion"
        )

    def test_retriever_has_dense_weight(self):
        """Verify retriever supports configurable dense_weight"""
        path = os.path.join(self.REPO_DIR, "src/rag/retriever.py")
        with open(path, "r") as f:
            content = f.read()

        assert "dense_weight" in content, "Should have configurable dense_weight"
        assert "0.7" in content, "Default dense_weight should be 0.7"

    def test_reranker_uses_cross_encoder(self):
        """Verify Reranker uses cross-encoder model"""
        path = os.path.join(self.REPO_DIR, "src/rag/reranker.py")
        with open(path, "r") as f:
            content = f.read()

        assert "Reranker" in content, "Must define Reranker class"
        assert "cross-encoder" in content or "CrossEncoder" in content, (
            "Should use cross-encoder for reranking"
        )

    def test_pipeline_uses_langgraph(self):
        """Verify pipeline uses LangGraph StateGraph"""
        path = os.path.join(self.REPO_DIR, "src/rag/pipeline.py")
        with open(path, "r") as f:
            content = f.read()

        assert "StateGraph" in content or "langgraph" in content, (
            "Pipeline should use LangGraph StateGraph"
        )

    def test_pipeline_has_four_nodes(self):
        """Verify pipeline defines retrieve, rerank, generate, cite_sources nodes"""
        path = os.path.join(self.REPO_DIR, "src/rag/pipeline.py")
        with open(path, "r") as f:
            content = f.read()

        expected = ["retrieve", "rerank", "generate", "cite_sources"]
        found = [n for n in expected if n in content]
        assert len(found) >= 3, (
            f"Pipeline should have 4 nodes. Found: {found}"
        )

    def test_prompts_has_citation_instructions(self):
        """Verify prompts include citation markers [1], [2]"""
        path = os.path.join(self.REPO_DIR, "src/rag/prompts.py")
        with open(path, "r") as f:
            content = f.read()

        assert "[1]" in content or "citation" in content.lower(), (
            "Prompts should include citation marker instructions"
        )

    def test_prompts_handles_insufficient_context(self):
        """Verify prompts instruct to say 'not enough information'"""
        path = os.path.join(self.REPO_DIR, "src/rag/prompts.py")
        with open(path, "r") as f:
            content = f.read()

        content_lower = content.lower()
        assert ("don't have enough" in content_lower or
                "not enough information" in content_lower or
                "cannot answer" in content_lower or
                "insufficient" in content_lower), (
            "Prompts should handle insufficient context case"
        )

    # === Functional Checks ===

    def test_all_python_files_parse(self):
        """Verify all Python files parse without syntax errors"""
        files = [
            "src/rag/__init__.py", "src/rag/ingestion.py",
            "src/rag/retriever.py", "src/rag/reranker.py",
            "src/rag/pipeline.py", "src/rag/prompts.py",
        ]
        for filename in files:
            path = os.path.join(self.REPO_DIR, filename)
            with open(path, "r") as f:
                source = f.read()
            try:
                ast.parse(source)
            except SyntaxError as e:
                pytest.fail(f"{filename} has syntax error: {e}")

    def test_init_exports(self):
        """Verify __init__.py exports main classes"""
        path = os.path.join(self.REPO_DIR, "src/rag/__init__.py")
        with open(path, "r") as f:
            content = f.read()

        assert "RAGPipeline" in content, "__init__.py should export RAGPipeline"
        assert "DocumentIngester" in content, "__init__.py should export DocumentIngester"
        assert "HybridRetriever" in content, "__init__.py should export HybridRetriever"

    def test_pipeline_tests_exist_and_parse(self):
        """Verify pipeline test files exist and parse"""
        test_files = [
            "tests/test_ingestion.py",
            "tests/test_retriever.py",
            "tests/test_pipeline.py",
        ]
        for filename in test_files:
            path = os.path.join(self.REPO_DIR, filename)
            assert os.path.exists(path), f"Test file {filename} not found"
            with open(path, "r") as f:
                source = f.read()
            try:
                ast.parse(source)
            except SyntaxError as e:
                pytest.fail(f"{filename} has syntax error: {e}")
