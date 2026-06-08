"""
Test skill: rag-implementation
Verify that the Agent correctly builds a RAG pipeline with hybrid retrieval
(FAISS + BM25 with RRF) in the LangChain community integrations.
"""

import os
import re
import ast
import sys
import pytest


class TestRagImplementation:
    REPO_DIR = "/workspace/langchain"

    DOC_PROCESSOR = "libs/community/langchain_community/rag/document_processor.py"
    HYBRID_RETRIEVER = "libs/community/langchain_community/rag/hybrid_retriever.py"
    QA_CHAIN = "libs/community/langchain_community/rag/qa_chain.py"
    INIT = "libs/community/langchain_community/rag/__init__.py"
    TESTS = "libs/community/tests/unit_tests/rag/test_rag_pipeline.py"

    def _read_file(self, rel_path):
        filepath = os.path.join(self.REPO_DIR, rel_path)
        with open(filepath) as f:
            return f.read()

    # === File Path Checks ===

    def test_document_processor_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.DOC_PROCESSOR)
        assert os.path.exists(filepath), f"document_processor.py not found at {filepath}"

    def test_hybrid_retriever_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.HYBRID_RETRIEVER)
        assert os.path.exists(filepath), f"hybrid_retriever.py not found at {filepath}"

    def test_qa_chain_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.QA_CHAIN)
        assert os.path.exists(filepath), f"qa_chain.py not found at {filepath}"

    def test_init_file_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.INIT)
        assert os.path.exists(filepath), f"__init__.py not found at {filepath}"

    def test_tests_file_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.TESTS)
        assert os.path.exists(filepath), f"Test file not found at {filepath}"

    # === Semantic Checks ===

    def test_doc_processor_class_defined(self):
        """Verify DocumentProcessor class with chunk_size and chunk_overlap"""
        content = self._read_file(self.DOC_PROCESSOR)
        assert "DocumentProcessor" in content, "Missing DocumentProcessor class"
        assert "chunk_size" in content, "Missing chunk_size parameter"
        assert "chunk_overlap" in content, "Missing chunk_overlap parameter"

    def test_doc_processor_loads_markdown(self):
        """Verify load_directory method loads .md files"""
        content = self._read_file(self.DOC_PROCESSOR)
        assert "load_directory" in content, "Missing load_directory method"
        has_md = bool(re.search(r'(\.md|markdown)', content, re.IGNORECASE))
        assert has_md, "load_directory missing .md file loading"

    def test_doc_processor_discards_short_chunks(self):
        """Verify chunks shorter than 50 chars are discarded"""
        content = self._read_file(self.DOC_PROCESSOR)
        has_min_length = bool(re.search(r'(50|min.*length|len.*<|short)', content))
        assert has_min_length, "DocumentProcessor missing short chunk discard (50 chars)"

    def test_doc_processor_uses_recursive_splitter(self):
        """Verify RecursiveCharacterTextSplitter is used for chunking"""
        content = self._read_file(self.DOC_PROCESSOR)
        assert "RecursiveCharacterTextSplitter" in content, \
            "Missing RecursiveCharacterTextSplitter usage"

    def test_hybrid_retriever_class_defined(self):
        """Verify HybridRetriever with dense/sparse search and RRF merge"""
        content = self._read_file(self.HYBRID_RETRIEVER)
        assert "HybridRetriever" in content, "Missing HybridRetriever class"
        assert "dense_search" in content, "Missing dense_search method"
        assert "sparse_search" in content, "Missing sparse_search method"
        assert "retrieve" in content, "Missing retrieve method"

    def test_hybrid_retriever_implements_rrf(self):
        """Verify Reciprocal Rank Fusion with constant 60"""
        content = self._read_file(self.HYBRID_RETRIEVER)
        has_rrf = bool(re.search(
            r'(reciprocal.*rank|rrf|1\s*/\s*\(rank.*\+.*60\)|rank.*\+.*60)',
            content,
            re.IGNORECASE,
        ))
        assert has_rrf, "HybridRetriever missing RRF implementation (1/(rank+60))"

    def test_hybrid_retriever_weights(self):
        """Verify dense_weight (0.6) and sparse_weight (0.4) defaults"""
        content = self._read_file(self.HYBRID_RETRIEVER)
        assert "dense_weight" in content, "Missing dense_weight parameter"
        assert "sparse_weight" in content, "Missing sparse_weight parameter"
        assert "0.6" in content, "Missing default dense_weight=0.6"
        assert "0.4" in content, "Missing default sparse_weight=0.4"

    def test_qa_chain_class_defined(self):
        """Verify QAChain with build_prompt method"""
        content = self._read_file(self.QA_CHAIN)
        assert "QAChain" in content, "Missing QAChain class"
        assert "build_prompt" in content, "Missing build_prompt method"

    def test_qa_chain_default_template(self):
        """Verify default prompt template structure"""
        content = self._read_file(self.QA_CHAIN)
        assert "context" in content.lower(), "Missing {context} in prompt template"
        assert "question" in content.lower(), "Missing {question} in prompt template"
        assert "---" in content, "Missing --- separator for context passages"

    def test_qa_chain_returns_source_documents(self):
        """Verify build_prompt returns source_documents and retrieval_scores"""
        content = self._read_file(self.QA_CHAIN)
        assert "source_documents" in content, "Missing source_documents in return"
        assert "retrieval_scores" in content, "Missing retrieval_scores in return"

    def test_init_exports_all_classes(self):
        """Verify __init__.py exports DocumentProcessor, HybridRetriever, QAChain"""
        content = self._read_file(self.INIT)
        for cls in ["DocumentProcessor", "HybridRetriever", "QAChain"]:
            assert cls in content, f"__init__.py missing export: {cls}"

    # === Functional Checks ===

    def test_all_files_valid_python(self):
        """Verify all Python files have valid syntax"""
        for path in [self.DOC_PROCESSOR, self.HYBRID_RETRIEVER,
                     self.QA_CHAIN, self.INIT]:
            filepath = os.path.join(self.REPO_DIR, path)
            with open(filepath) as f:
                try:
                    ast.parse(f.read())
                except SyntaxError as e:
                    pytest.fail(f"{path} syntax error: {e}")

    def test_bm25_integration(self):
        """Verify BM25 sparse search is implemented"""
        content = self._read_file(self.HYBRID_RETRIEVER)
        has_bm25 = bool(re.search(r'(BM25|bm25|BM25Okapi|rank_bm25)', content))
        assert has_bm25, "HybridRetriever missing BM25 implementation"

    def test_tests_cover_key_components(self):
        """Verify tests cover chunking, RRF computation, and prompt formatting"""
        content = self._read_file(self.TESTS)
        tree = ast.parse(content)
        test_funcs = [
            n.name for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
        ]
        assert len(test_funcs) >= 5, \
            f"Expected at least 5 tests, found {len(test_funcs)}"
        content_lower = content.lower()
        assert "chunk" in content_lower, "Tests missing chunking coverage"
        assert "rrf" in content_lower or "retriev" in content_lower, \
            "Tests missing retrieval/RRF coverage"
