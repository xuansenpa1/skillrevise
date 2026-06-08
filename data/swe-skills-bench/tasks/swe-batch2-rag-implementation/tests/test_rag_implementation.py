"""
Test skill: rag-implementation
Verify that the Agent creates an end-to-end RAG demo for LangChain
including document loading, chunking, vector store, retrieval,
and answer generation with source references.
"""

import os
import re
import ast
import subprocess
import pytest


class TestRagImplementation:
    REPO_DIR = "/workspace/langchain"

    # === File Path Checks ===

    def test_rag_demo_exists(self):
        """Verify examples/rag_demo.py exists"""
        path = os.path.join(self.REPO_DIR, "examples/rag_demo.py")
        assert os.path.exists(path), f"rag_demo.py not found at {path}"

    # === Semantic Checks ===

    def test_document_loading(self):
        """Verify document loading from local source"""
        path = os.path.join(self.REPO_DIR, "examples/rag_demo.py")
        with open(path) as f:
            content = f.read()

        load_indicators = [
            "load", "document", "open(", "read",
            "TextLoader", "DirectoryLoader", "markdown",
        ]
        found = [ind for ind in load_indicators if ind in content]
        assert len(found) >= 2, (
            f"Should load documents from a local source. Found: {found}"
        )

    def test_chunking(self):
        """Verify document splitting into configurable chunks"""
        path = os.path.join(self.REPO_DIR, "examples/rag_demo.py")
        with open(path) as f:
            content = f.read()

        chunk_indicators = [
            "chunk", "split", "TextSplitter", "RecursiveCharacterTextSplitter",
            "chunk_size", "chunk_overlap", "overlap",
        ]
        found = [ind for ind in chunk_indicators if ind in content]
        assert len(found) >= 2, (
            f"Should split documents into chunks. Found: {found}"
        )

    def test_vector_store(self):
        """Verify vector store creation from document chunks"""
        path = os.path.join(self.REPO_DIR, "examples/rag_demo.py")
        with open(path) as f:
            content = f.read()

        vs_indicators = [
            "vector", "embed", "VectorStore", "FAISS",
            "Chroma", "vectorstore", "from_documents",
            "from_texts", "embedding",
        ]
        found = [ind for ind in vs_indicators if ind in content]
        assert len(found) >= 2, (
            f"Should create a vector store. Found: {found}"
        )

    def test_similarity_search(self):
        """Verify similarity search against the vector store"""
        path = os.path.join(self.REPO_DIR, "examples/rag_demo.py")
        with open(path) as f:
            content = f.read()

        search_indicators = [
            "similarity_search", "search", "query", "retrieve",
            "retriever", "as_retriever", "top_k", "k=",
        ]
        found = [ind for ind in search_indicators if ind in content]
        assert len(found) >= 2, (
            f"Should perform similarity search. Found: {found}"
        )

    def test_context_augmented_prompt(self):
        """Verify prompt includes retrieved context with user question"""
        path = os.path.join(self.REPO_DIR, "examples/rag_demo.py")
        with open(path) as f:
            content = f.read().lower()

        prompt_indicators = [
            "context", "question", "prompt", "template",
            "retrieved", "answer", "based on",
        ]
        found = [ind for ind in prompt_indicators if ind in content]
        assert len(found) >= 3, (
            f"Should construct context-augmented prompt. Found: {found}"
        )

    def test_answer_generation(self):
        """Verify LLM answer generation"""
        path = os.path.join(self.REPO_DIR, "examples/rag_demo.py")
        with open(path) as f:
            content = f.read()

        llm_indicators = [
            "LLM", "ChatOpenAI", "OpenAI", "invoke",
            "generate", "predict", "llm", "chat",
            "chain", "RunnableSequence",
        ]
        found = [ind for ind in llm_indicators if ind in content]
        assert len(found) >= 1, (
            f"Should use an LLM for answer generation. Found: {found}"
        )

    def test_source_references(self):
        """Verify answer includes source references"""
        path = os.path.join(self.REPO_DIR, "examples/rag_demo.py")
        with open(path) as f:
            content = f.read().lower()

        source_indicators = [
            "source", "reference", "metadata", "page_content",
            "document", "cite",
        ]
        found = [ind for ind in source_indicators if ind in content]
        assert len(found) >= 2, (
            f"Should include source references. Found: {found}"
        )

    def test_configurable_parameters(self):
        """Verify chunk_size, overlap, top_k are configurable"""
        path = os.path.join(self.REPO_DIR, "examples/rag_demo.py")
        with open(path) as f:
            content = f.read()

        config_indicators = [
            "chunk_size", "chunk_overlap", "top_k", "k=",
            "config", "argparse", "parameter",
        ]
        found = [ind for ind in config_indicators if ind in content]
        assert len(found) >= 2, (
            f"Chunk size, overlap, top_k should be configurable. Found: {found}"
        )

    # === Functional Checks ===

    def test_script_valid_python(self):
        """Verify rag_demo.py is valid Python syntax"""
        path = os.path.join(self.REPO_DIR, "examples/rag_demo.py")
        with open(path) as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"rag_demo.py has syntax errors: {e}")

    def test_has_main_entry_point(self):
        """Verify script has __main__ entry point"""
        path = os.path.join(self.REPO_DIR, "examples/rag_demo.py")
        with open(path) as f:
            content = f.read()

        assert '__name__' in content and '__main__' in content, (
            "Script should have a __main__ entry point"
        )

    def test_defines_pipeline_functions(self):
        """Verify script defines reusable pipeline functions"""
        path = os.path.join(self.REPO_DIR, "examples/rag_demo.py")
        with open(path) as f:
            source = f.read()

        tree = ast.parse(source)
        func_names = [
            node.name for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        assert len(func_names) >= 3, (
            f"Script should define pipeline functions. Found: {func_names}"
        )
