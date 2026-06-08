"""
Test skill: rag-implementation
Verify that the Agent creates a RAG pipeline with DocumentChunker, HybridRetriever (RRF),
CrossEncoderReranker, and CitationExtractor for LangChain.
"""

import os
import subprocess
import ast
import re
import pytest


class TestRagImplementation:
    REPO_DIR = "/workspace/langchain"

    # === File Path Checks ===

    def test_rag_files_exist(self):
        """Verify RAG pipeline files exist"""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root or "node_modules" in root:
                continue
            for f in files:
                if f.endswith(".py") and ("rag" in f.lower() or "retriev" in f.lower() or "chunk" in f.lower()):
                    fpath = os.path.join(root, f)
                    with open(fpath) as fh:
                        content = fh.read()
                    if "Chunker" in content or "Retriever" in content or "Reranker" in content:
                        found = True
                        break
            if found:
                break
        assert found, "RAG pipeline files not found"

    # === Semantic Checks ===

    def test_document_chunker_defined(self):
        """Verify DocumentChunker class is defined"""
        content = self._find_content()
        has_chunker = "DocumentChunker" in content or "Chunker" in content
        assert has_chunker, "DocumentChunker not found"

    def test_hybrid_retriever_defined(self):
        """Verify HybridRetriever class is defined"""
        content = self._find_content()
        has_hybrid = "HybridRetriever" in content or "hybrid" in content.lower()
        assert has_hybrid, "HybridRetriever not found"

    def test_rrf_fusion_implemented(self):
        """Verify Reciprocal Rank Fusion (RRF) is implemented"""
        content = self._find_content()
        content_lower = content.lower()
        has_rrf = "rrf" in content_lower or "reciprocal_rank" in content_lower or "rank_fusion" in content_lower
        assert has_rrf, "RRF (Reciprocal Rank Fusion) not found"

    def test_cross_encoder_reranker_defined(self):
        """Verify CrossEncoderReranker class is defined"""
        content = self._find_content()
        has_reranker = "CrossEncoder" in content or "Reranker" in content or "rerank" in content.lower()
        assert has_reranker, "CrossEncoderReranker not found"

    def test_citation_extractor_defined(self):
        """Verify CitationExtractor class is defined"""
        content = self._find_content()
        has_citation = "CitationExtractor" in content or "citation" in content.lower()
        assert has_citation, "CitationExtractor not found"

    def test_chunker_has_overlap_parameter(self):
        """Verify DocumentChunker supports chunk overlap"""
        content = self._find_content()
        content_lower = content.lower()
        has_overlap = "overlap" in content_lower or "stride" in content_lower
        assert has_overlap, "DocumentChunker missing overlap parameter"

    # === Functional Checks ===

    def test_all_rag_files_parse(self):
        """Verify all RAG files have valid Python syntax"""
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".py") and ("rag" in f.lower() or "retriev" in f.lower() or "chunk" in f.lower() or "rerank" in f.lower() or "citation" in f.lower()):
                    fpath = os.path.join(root, f)
                    with open(fpath) as fh:
                        source = fh.read()
                    try:
                        ast.parse(source)
                    except SyntaxError as e:
                        pytest.fail(f"Syntax error in {fpath}: {e}")

    def test_rag_imports_langchain(self):
        """Verify RAG files import from langchain"""
        content = self._find_content()
        has_langchain = "langchain" in content
        assert has_langchain, "RAG files do not import from langchain"

    def test_retriever_has_retrieve_method(self):
        """Verify HybridRetriever defines a retrieve/search method"""
        content = self._find_content()
        has_method = (
            "def retrieve" in content
            or "def search" in content
            or "def get_relevant" in content
            or "_get_relevant_documents" in content
        )
        assert has_method, "HybridRetriever missing retrieve method"

    def _find_content(self):
        """Helper to find RAG-related content"""
        all_content = ""
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root or "node_modules" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath) as fh:
                            content = fh.read()
                        if any(kw in content for kw in ["DocumentChunker", "HybridRetriever", "CrossEncoder", "CitationExtractor", "Reranker"]):
                            all_content += content + "\n"
                    except (UnicodeDecodeError, PermissionError):
                        continue
        return all_content
