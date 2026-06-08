"""
Tests for the rag-implementation skill.

Validates that a hybrid RAG retrieval pipeline with reranking was implemented
for LangChain, including HybridRetriever with RRF, MultiQueryRetriever,
Reranker, citation tracking, and RecursiveChunker.

Repo: langchain (https://github.com/langchain-ai/langchain)
"""

import ast
import os
import re
import subprocess
import sys

REPO_DIR = "/workspace/langchain"


class TestFilePathCheck:
    """Verify that all required files were created."""

    def test_hybrid_retriever_file_exists(self):
        path = os.path.join(
            REPO_DIR, "libs", "core", "langchain_core", "retrievers", "hybrid_retriever.py"
        )
        assert os.path.isfile(path), f"Expected hybrid_retriever.py at {path}"

    def test_multi_query_file_exists(self):
        path = os.path.join(
            REPO_DIR, "libs", "core", "langchain_core", "retrievers", "multi_query.py"
        )
        assert os.path.isfile(path), f"Expected multi_query.py at {path}"

    def test_reranker_file_exists(self):
        path = os.path.join(
            REPO_DIR, "libs", "core", "langchain_core", "retrievers", "reranker.py"
        )
        assert os.path.isfile(path), f"Expected reranker.py at {path}"

    def test_test_file_exists(self):
        path = os.path.join(
            REPO_DIR, "libs", "core", "tests", "unit_tests", "retrievers",
            "test_hybrid_retriever.py",
        )
        assert os.path.isfile(path), f"Expected test_hybrid_retriever.py at {path}"


class TestSemanticHybridRetriever:
    """Verify HybridRetriever with Reciprocal Rank Fusion."""

    def _read_hybrid(self):
        path = os.path.join(
            REPO_DIR, "libs", "core", "langchain_core", "retrievers", "hybrid_retriever.py"
        )
        with open(path, "r") as f:
            return f.read()

    def test_hybrid_retriever_class(self):
        content = self._read_hybrid()
        assert re.search(r"class\s+HybridRetriever", content), (
            "Expected HybridRetriever class"
        )

    def test_dense_retriever_parameter(self):
        content = self._read_hybrid()
        assert re.search(r"dense_retriever|dense", content), (
            "Expected dense_retriever parameter"
        )

    def test_sparse_retriever_parameter(self):
        content = self._read_hybrid()
        assert re.search(r"sparse_retriever|sparse", content), (
            "Expected sparse_retriever parameter"
        )

    def test_rrf_implementation(self):
        """Reciprocal Rank Fusion: score = sum(1/(k + rank))."""
        content = self._read_hybrid()
        assert re.search(r"rrf|reciprocal.*rank|1\s*/\s*\(.*k.*\+.*rank", content, re.IGNORECASE), (
            "Expected Reciprocal Rank Fusion (RRF) implementation"
        )

    def test_rrf_k_parameter(self):
        """RRF constant k should default to 60."""
        content = self._read_hybrid()
        assert "60" in content, (
            "Expected RRF k constant default of 60"
        )

    def test_deduplication(self):
        """Documents from both retrievers should be deduplicated."""
        content = self._read_hybrid()
        assert re.search(r"dedup|deduplicate|hash|seen|unique", content, re.IGNORECASE), (
            "Expected document deduplication logic"
        )

    def test_retrieval_method_metadata(self):
        content = self._read_hybrid()
        assert re.search(r"retrieval_method|dense|sparse|hybrid", content), (
            "Expected retrieval_method metadata on documents"
        )


class TestSemanticMultiQuery:
    """Verify MultiQueryRetriever with query expansion."""

    def _read_multi(self):
        path = os.path.join(
            REPO_DIR, "libs", "core", "langchain_core", "retrievers", "multi_query.py"
        )
        with open(path, "r") as f:
            return f.read()

    def test_multi_query_retriever_class(self):
        content = self._read_multi()
        assert re.search(r"class\s+MultiQueryRetriever", content), (
            "Expected MultiQueryRetriever class"
        )

    def test_query_generator_parameter(self):
        content = self._read_multi()
        assert re.search(r"query_generator|generate.*quer", content, re.IGNORECASE), (
            "Expected query_generator parameter or method"
        )

    def test_merge_results(self):
        content = self._read_multi()
        assert re.search(r"merge|rrf|fusion|combine", content, re.IGNORECASE), (
            "Expected result merging logic in MultiQueryRetriever"
        )

    def test_default_num_queries(self):
        """Should generate 3 query variations by default."""
        content = self._read_multi()
        assert "3" in content, (
            "Expected default of 3 query variations"
        )


class TestSemanticReranker:
    """Verify Reranker class with scoring and filtering."""

    def _read_reranker(self):
        path = os.path.join(
            REPO_DIR, "libs", "core", "langchain_core", "retrievers", "reranker.py"
        )
        with open(path, "r") as f:
            return f.read()

    def test_reranker_class(self):
        content = self._read_reranker()
        assert re.search(r"class\s+Reranker", content), (
            "Expected Reranker class"
        )

    def test_scoring_function_parameter(self):
        content = self._read_reranker()
        assert re.search(r"scoring_function|scorer|score_fn", content), (
            "Expected scoring_function parameter in Reranker"
        )

    def test_min_score_threshold(self):
        content = self._read_reranker()
        assert re.search(r"min_score", content), (
            "Expected min_score threshold parameter"
        )

    def test_rerank_score_metadata(self):
        content = self._read_reranker()
        assert re.search(r"rerank_score", content), (
            "Expected rerank_score attached to document metadata"
        )


class TestSemanticCitationTracking:
    """Verify citation formatting and metadata."""

    def _read_all_sources(self):
        content = ""
        for fname in ["hybrid_retriever.py", "reranker.py"]:
            path = os.path.join(
                REPO_DIR, "libs", "core", "langchain_core", "retrievers", fname
            )
            if os.path.isfile(path):
                with open(path, "r") as f:
                    content += f.read()
        return content

    def test_format_citations_function(self):
        content = self._read_all_sources()
        assert re.search(r"def\s+format_citations", content), (
            "Expected format_citations function"
        )

    def test_source_metadata(self):
        content = self._read_all_sources()
        assert re.search(r'source|metadata\[.*source', content), (
            "Expected source metadata on documents"
        )

    def test_rrf_score_metadata(self):
        content = self._read_all_sources()
        assert re.search(r"rrf_score", content), (
            "Expected rrf_score in document metadata"
        )


class TestSemanticChunker:
    """Verify RecursiveChunker implementation."""

    def _read_all_sources(self):
        content = ""
        for fname in ["hybrid_retriever.py", "multi_query.py", "reranker.py"]:
            path = os.path.join(
                REPO_DIR, "libs", "core", "langchain_core", "retrievers", fname
            )
            if os.path.isfile(path):
                with open(path, "r") as f:
                    content += f.read()
        return content

    def test_recursive_chunker_class(self):
        content = self._read_all_sources()
        assert re.search(r"class\s+RecursiveChunker", content), (
            "Expected RecursiveChunker class"
        )

    def test_chunk_size_parameter(self):
        content = self._read_all_sources()
        assert re.search(r"chunk_size", content), (
            "Expected chunk_size parameter in RecursiveChunker"
        )

    def test_chunk_overlap_parameter(self):
        content = self._read_all_sources()
        assert re.search(r"chunk_overlap|overlap", content), (
            "Expected chunk_overlap parameter"
        )

    def test_chunk_metadata(self):
        """Each chunk should have chunk_index, start_char, end_char."""
        content = self._read_all_sources()
        assert re.search(r"chunk_index|start_char|end_char", content), (
            "Expected chunk metadata (chunk_index, start_char, end_char)"
        )


class TestFunctionalPythonSyntax:
    """Validate Python syntax of all created files."""

    def _check_syntax(self, filepath):
        with open(filepath, "r") as f:
            source = f.read()
        ast.parse(source)

    def test_hybrid_retriever_syntax(self):
        self._check_syntax(
            os.path.join(
                REPO_DIR, "libs", "core", "langchain_core", "retrievers",
                "hybrid_retriever.py",
            )
        )

    def test_multi_query_syntax(self):
        self._check_syntax(
            os.path.join(
                REPO_DIR, "libs", "core", "langchain_core", "retrievers", "multi_query.py"
            )
        )

    def test_reranker_syntax(self):
        self._check_syntax(
            os.path.join(
                REPO_DIR, "libs", "core", "langchain_core", "retrievers", "reranker.py"
            )
        )

    def test_test_file_syntax(self):
        self._check_syntax(
            os.path.join(
                REPO_DIR, "libs", "core", "tests", "unit_tests", "retrievers",
                "test_hybrid_retriever.py",
            )
        )


class TestFunctionalAgentTests:
    """Verify the agent's own tests pass."""

    def test_sufficient_test_count(self):
        path = os.path.join(
            REPO_DIR, "libs", "core", "tests", "unit_tests", "retrievers",
            "test_hybrid_retriever.py",
        )
        with open(path, "r") as f:
            content = f.read()
        test_count = len(re.findall(r"def\s+test_", content))
        assert test_count >= 5, (
            f"Expected at least 5 test functions, found {test_count}"
        )

    def test_agent_tests_pass(self):
        result = subprocess.run(
            [sys.executable, "-m", "pytest",
             "libs/core/tests/unit_tests/retrievers/test_hybrid_retriever.py",
             "-v", "--tb=short"],
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"Agent's RAG tests failed:\n{result.stdout[-1000:]}\n{result.stderr[-500:]}"
        )
