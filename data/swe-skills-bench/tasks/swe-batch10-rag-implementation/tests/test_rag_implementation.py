"""
Test skill: rag-implementation
Verify that the Agent correctly implements a hybrid RAG pipeline with
reranking, parent-chunk retrieval, and LangGraph orchestration.
"""

import os
import re
import ast
import subprocess
import pytest


class TestRagImplementation:
    REPO_DIR = "/workspace/langchain"

    # === File Path Checks ===

    def test_hybrid_retriever_exists(self):
        """Verify hybrid_rerank_retriever.py was created"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/retrievers/hybrid_rerank_retriever.py",
        )
        assert os.path.exists(path), f"hybrid_rerank_retriever.py not found at {path}"

    def test_parent_chunk_retriever_exists(self):
        """Verify parent_chunk_retriever.py was created"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/retrievers/parent_chunk_retriever.py",
        )
        assert os.path.exists(path), f"parent_chunk_retriever.py not found at {path}"

    def test_rag_pipeline_exists(self):
        """Verify rag_pipeline.py was created"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/graphs/rag_pipeline.py",
        )
        assert os.path.exists(path), f"rag_pipeline.py not found at {path}"

    def test_chunking_utils_exists(self):
        """Verify chunking.py was created"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/utils/chunking.py",
        )
        assert os.path.exists(path), f"chunking.py not found at {path}"

    def test_hybrid_retriever_test_exists(self):
        """Verify hybrid retriever test file was created"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/tests/unit_tests/retrievers/test_hybrid_rerank_retriever.py",
        )
        assert os.path.exists(path), f"test_hybrid_rerank_retriever.py not found"

    def test_parent_chunk_test_exists(self):
        """Verify parent chunk retriever test file was created"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/tests/unit_tests/retrievers/test_parent_chunk_retriever.py",
        )
        assert os.path.exists(path), f"test_parent_chunk_retriever.py not found"

    def test_rag_pipeline_test_exists(self):
        """Verify RAG pipeline test file was created"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/tests/unit_tests/graphs/test_rag_pipeline.py",
        )
        assert os.path.exists(path), f"test_rag_pipeline.py not found"

    # === Semantic Checks: HybridRerankRetriever ===

    def test_hybrid_retriever_extends_base(self):
        """Verify HybridRerankRetriever extends BaseRetriever"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/retrievers/hybrid_rerank_retriever.py",
        )
        with open(path) as f:
            content = f.read()
        assert "BaseRetriever" in content, (
            "HybridRerankRetriever should extend BaseRetriever"
        )

    def test_hybrid_has_rrf_fusion(self):
        """Verify Reciprocal Rank Fusion is implemented"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/retrievers/hybrid_rerank_retriever.py",
        )
        with open(path) as f:
            content = f.read()
        assert "rrf" in content.lower() or "reciprocal" in content.lower() or "rank" in content.lower(), (
            "Should implement Reciprocal Rank Fusion"
        )

    def test_hybrid_has_dense_sparse_weights(self):
        """Verify dense_weight and sparse_weight parameters"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/retrievers/hybrid_rerank_retriever.py",
        )
        with open(path) as f:
            content = f.read()
        assert "dense_weight" in content, "Should have dense_weight parameter"
        assert "sparse_weight" in content, "Should have sparse_weight parameter"

    def test_hybrid_validates_weight_sum(self):
        """Verify weights must sum to 1.0"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/retrievers/hybrid_rerank_retriever.py",
        )
        with open(path) as f:
            content = f.read()
        assert "ValueError" in content, (
            "Should raise ValueError if weights don't sum to 1.0"
        )

    def test_hybrid_has_rerank_option(self):
        """Verify optional cross-encoder reranking"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/retrievers/hybrid_rerank_retriever.py",
        )
        with open(path) as f:
            content = f.read()
        assert "rerank" in content.lower(), (
            "Should support optional reranking"
        )

    def test_hybrid_sets_retrieval_score(self):
        """Verify retrieval_score is set in document metadata"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/retrievers/hybrid_rerank_retriever.py",
        )
        with open(path) as f:
            content = f.read()
        assert "retrieval_score" in content, (
            "Should set metadata['retrieval_score'] on results"
        )

    # === Semantic Checks: ParentChunkRetriever ===

    def test_parent_chunk_has_add_documents(self):
        """Verify add_documents method exists"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/retrievers/parent_chunk_retriever.py",
        )
        with open(path) as f:
            content = f.read()
        assert "def add_documents(" in content, (
            "ParentChunkRetriever should have add_documents method"
        )

    def test_parent_chunk_validates_sizes(self):
        """Verify child_chunk_size < parent_chunk_size validation"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/retrievers/parent_chunk_retriever.py",
        )
        with open(path) as f:
            content = f.read()
        assert "ValueError" in content, (
            "Should raise ValueError if child_chunk_size >= parent_chunk_size"
        )

    def test_parent_chunk_uses_parent_id(self):
        """Verify parent_id is used in metadata for mapping"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/retrievers/parent_chunk_retriever.py",
        )
        with open(path) as f:
            content = f.read()
        assert "parent_id" in content, (
            "Should use parent_id in child chunk metadata"
        )

    # === Semantic Checks: RAG Pipeline ===

    def test_rag_state_defined(self):
        """Verify RAGState TypedDict is defined"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/graphs/rag_pipeline.py",
        )
        with open(path) as f:
            content = f.read()
        assert "RAGState" in content, "RAGState TypedDict should be defined"

    def test_rag_has_state_graph(self):
        """Verify StateGraph is used"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/graphs/rag_pipeline.py",
        )
        with open(path) as f:
            content = f.read()
        assert "StateGraph" in content, "Should use StateGraph from langgraph"

    def test_rag_has_build_function(self):
        """Verify build_rag_graph factory function exists"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/graphs/rag_pipeline.py",
        )
        with open(path) as f:
            content = f.read()
        assert "def build_rag_graph(" in content, (
            "Should have build_rag_graph factory function"
        )

    def test_rag_has_retrieve_generate_nodes(self):
        """Verify graph has retrieve and generate nodes"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/graphs/rag_pipeline.py",
        )
        with open(path) as f:
            content = f.read()
        assert "retrieve" in content, "Graph should have retrieve node"
        assert "generate" in content, "Graph should have generate node"

    # === Semantic Checks: Chunking Utilities ===

    def test_recursive_split_defined(self):
        """Verify recursive_split function is defined"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/utils/chunking.py",
        )
        with open(path) as f:
            content = f.read()
        assert "def recursive_split(" in content, (
            "recursive_split function should be defined"
        )

    def test_token_split_defined(self):
        """Verify token_split function is defined"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/utils/chunking.py",
        )
        with open(path) as f:
            content = f.read()
        assert "def token_split(" in content, (
            "token_split function should be defined"
        )

    def test_markdown_split_defined(self):
        """Verify markdown_split function is defined"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/utils/chunking.py",
        )
        with open(path) as f:
            content = f.read()
        assert "def markdown_split(" in content, (
            "markdown_split function should be defined"
        )

    def test_chunking_validates_overlap(self):
        """Verify ValueError for chunk_overlap >= chunk_size"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/utils/chunking.py",
        )
        with open(path) as f:
            content = f.read()
        assert "ValueError" in content, (
            "Should raise ValueError for invalid overlap/size"
        )

    # === Functional Checks ===

    def test_hybrid_retriever_parses(self):
        """Verify hybrid_rerank_retriever.py has valid Python syntax"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/retrievers/hybrid_rerank_retriever.py",
        )
        with open(path) as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"hybrid_rerank_retriever.py has syntax error: {e}")

    def test_chunking_parses(self):
        """Verify chunking.py has valid Python syntax"""
        path = os.path.join(
            self.REPO_DIR,
            "libs/community/langchain_community/utils/chunking.py",
        )
        with open(path) as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"chunking.py has syntax error: {e}")

    def test_hybrid_retriever_tests_pass(self):
        """Verify hybrid retriever tests pass"""
        result = subprocess.run(
            [
                "python", "-m", "pytest",
                "libs/community/tests/unit_tests/retrievers/test_hybrid_rerank_retriever.py",
                "-v", "--tb=short",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"Hybrid retriever tests failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_parent_chunk_tests_pass(self):
        """Verify parent chunk retriever tests pass"""
        result = subprocess.run(
            [
                "python", "-m", "pytest",
                "libs/community/tests/unit_tests/retrievers/test_parent_chunk_retriever.py",
                "-v", "--tb=short",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"Parent chunk tests failed:\n{result.stdout}\n{result.stderr}"
        )
