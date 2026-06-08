"""
Test skill: rag-implementation
Verify that the Agent implements a Modular RAG Pipeline with Hybrid Retrieval
in LangChain — HybridRetriever (RRF + weighted score), SemanticChunker, and
RAGChain with source attribution.
"""

import os
import re
import ast
import subprocess
import pytest


class TestRagImplementation:
    REPO_DIR = "/workspace/langchain"

    # ────────────────── helpers ──────────────────

    def _read(self, rel_path):
        fpath = os.path.join(self.REPO_DIR, rel_path)
        with open(fpath, "r") as f:
            return f.read()

    def _exists(self, rel_path):
        return os.path.isfile(os.path.join(self.REPO_DIR, rel_path))

    def _parse(self, rel_path):
        fpath = os.path.join(self.REPO_DIR, rel_path)
        with open(fpath, "r") as f:
            return ast.parse(f.read())

    # === File Path Checks ===

    def test_hybrid_retriever_exists(self):
        """hybrid_retriever.py must exist"""
        assert self._exists(
            "libs/langchain/langchain/retrievers/hybrid_retriever.py"
        )

    def test_semantic_chunker_exists(self):
        """semantic_chunker.py must exist"""
        assert self._exists(
            "libs/langchain/langchain/text_splitter/semantic_chunker.py"
        )

    def test_rag_chain_exists(self):
        """rag_chain.py must exist"""
        assert self._exists(
            "libs/langchain/langchain/chains/rag_chain.py"
        )

    def test_hybrid_retriever_test_exists(self):
        """Unit test for hybrid retriever must exist"""
        assert self._exists(
            "libs/langchain/tests/unit_tests/retrievers/test_hybrid_retriever.py"
        )

    def test_rag_chain_test_exists(self):
        """Unit test for RAG chain must exist"""
        assert self._exists(
            "libs/langchain/tests/unit_tests/chains/test_rag_chain.py"
        )

    # === Semantic Checks — HybridRetriever ===

    def test_hybrid_retriever_class(self):
        """HybridRetriever class must be defined"""
        src = self._read(
            "libs/langchain/langchain/retrievers/hybrid_retriever.py"
        )
        assert re.search(r'class\s+HybridRetriever\b', src), (
            "HybridRetriever class not found"
        )

    def test_hybrid_inherits_base_retriever(self):
        """HybridRetriever must inherit from BaseRetriever"""
        src = self._read(
            "libs/langchain/langchain/retrievers/hybrid_retriever.py"
        )
        assert "BaseRetriever" in src, (
            "HybridRetriever should inherit from BaseRetriever"
        )

    def test_hybrid_get_relevant_documents(self):
        """HybridRetriever must implement _get_relevant_documents"""
        src = self._read(
            "libs/langchain/langchain/retrievers/hybrid_retriever.py"
        )
        assert "_get_relevant_documents" in src, (
            "_get_relevant_documents not found"
        )

    def test_rrf_fusion_constant(self):
        """RRF fusion must use k_rrf constant (typically 60)"""
        src = self._read(
            "libs/langchain/langchain/retrievers/hybrid_retriever.py"
        )
        assert "60" in src or "k_rrf" in src, (
            "RRF constant k_rrf=60 not found"
        )

    def test_fusion_methods_supported(self):
        """Both 'rrf' and 'weighted_score' fusion methods must be supported"""
        src = self._read(
            "libs/langchain/langchain/retrievers/hybrid_retriever.py"
        )
        assert "rrf" in src and "weighted_score" in src, (
            "Must support both 'rrf' and 'weighted_score' fusion methods"
        )

    def test_retrieval_score_in_metadata(self):
        """Fusion score should be attached as metadata['retrieval_score']"""
        src = self._read(
            "libs/langchain/langchain/retrievers/hybrid_retriever.py"
        )
        assert "retrieval_score" in src, (
            "retrieval_score not attached to document metadata"
        )

    # === Semantic Checks — SemanticChunker ===

    def test_semantic_chunker_class(self):
        """SemanticChunker class must be defined"""
        src = self._read(
            "libs/langchain/langchain/text_splitter/semantic_chunker.py"
        )
        assert re.search(r'class\s+SemanticChunker\b', src), (
            "SemanticChunker class not found"
        )

    def test_split_text_method(self):
        """SemanticChunker must have split_text() method"""
        src = self._read(
            "libs/langchain/langchain/text_splitter/semantic_chunker.py"
        )
        assert re.search(r'def\s+split_text\s*\(\s*self', src), (
            "split_text() method not found"
        )

    def test_split_documents_method(self):
        """SemanticChunker must have split_documents() method"""
        src = self._read(
            "libs/langchain/langchain/text_splitter/semantic_chunker.py"
        )
        assert re.search(r'def\s+split_documents\s*\(\s*self', src), (
            "split_documents() method not found"
        )

    def test_similarity_threshold_param(self):
        """SemanticChunker must use similarity_threshold for split decisions"""
        src = self._read(
            "libs/langchain/langchain/text_splitter/semantic_chunker.py"
        )
        assert "similarity_threshold" in src, (
            "similarity_threshold parameter not found"
        )

    def test_overlap_sentences_param(self):
        """SemanticChunker must support overlap_sentences for chunk overlap"""
        src = self._read(
            "libs/langchain/langchain/text_splitter/semantic_chunker.py"
        )
        assert "overlap_sentences" in src, (
            "overlap_sentences parameter not found"
        )

    # === Semantic Checks — RAGChain ===

    def test_rag_chain_class(self):
        """RAGChain class must be defined"""
        src = self._read("libs/langchain/langchain/chains/rag_chain.py")
        assert re.search(r'class\s+RAGChain\b', src), (
            "RAGChain class not found"
        )

    def test_rag_invoke_method(self):
        """RAGChain must have invoke() method"""
        src = self._read("libs/langchain/langchain/chains/rag_chain.py")
        assert re.search(r'def\s+invoke\s*\(\s*self', src), (
            "invoke() method not found"
        )

    def test_rag_response_dataclass(self):
        """RAGResponse dataclass must be defined"""
        src = self._read("libs/langchain/langchain/chains/rag_chain.py")
        assert "RAGResponse" in src, "RAGResponse dataclass not found"

    def test_rag_response_fields(self):
        """RAGResponse must have answer, sources, query, context_length"""
        src = self._read("libs/langchain/langchain/chains/rag_chain.py")
        for field in ["answer", "sources", "query", "context_length"]:
            assert field in src, f"RAGResponse missing field: {field}"

    def test_source_numbering(self):
        """Context assembly should number documents [1], [2], etc."""
        src = self._read("libs/langchain/langchain/chains/rag_chain.py")
        assert "[1]" in src or "\\[{i" in src or "f\"[{" in src, (
            "Source document numbering not found"
        )

    def test_max_context_tokens_param(self):
        """RAGChain must respect max_context_tokens"""
        src = self._read("libs/langchain/langchain/chains/rag_chain.py")
        assert "max_context_tokens" in src, (
            "max_context_tokens parameter not found"
        )

    def test_streaming_method(self):
        """RAGChain must have invoke_with_streaming method"""
        src = self._read("libs/langchain/langchain/chains/rag_chain.py")
        assert "invoke_with_streaming" in src or "stream" in src, (
            "Streaming method not found"
        )

    # === Functional Checks ===

    def test_hybrid_retriever_importable(self):
        """HybridRetriever must be importable"""
        result = subprocess.run(
            ["python", "-c",
             "from langchain.retrievers.hybrid_retriever import HybridRetriever; "
             "print('OK')"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=30,
        )
        assert "OK" in result.stdout, (
            f"Import failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_semantic_chunker_importable(self):
        """SemanticChunker must be importable"""
        result = subprocess.run(
            ["python", "-c",
             "from langchain.text_splitter.semantic_chunker import SemanticChunker; "
             "print('OK')"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=30,
        )
        assert "OK" in result.stdout, (
            f"Import failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_rag_chain_importable(self):
        """RAGChain must be importable"""
        result = subprocess.run(
            ["python", "-c",
             "from langchain.chains.rag_chain import RAGChain, RAGResponse; "
             "print('OK')"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=30,
        )
        assert "OK" in result.stdout, (
            f"Import failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_hybrid_retriever_unit_tests_pass(self):
        """Hybrid retriever unit tests must pass"""
        result = subprocess.run(
            ["python", "-m", "pytest",
             "libs/langchain/tests/unit_tests/retrievers/test_hybrid_retriever.py",
             "-v", "--tb=short"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, (
            f"Tests failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_rag_chain_unit_tests_pass(self):
        """RAG chain unit tests must pass"""
        result = subprocess.run(
            ["python", "-m", "pytest",
             "libs/langchain/tests/unit_tests/chains/test_rag_chain.py",
             "-v", "--tb=short"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, (
            f"Tests failed:\n{result.stdout}\n{result.stderr}"
        )
