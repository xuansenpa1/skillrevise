"""
Test for 'rag-implementation' skill — RAG Implementation Framework
Validates that the Agent created an end-to-end RAG demo in the LangChain repo.
"""

import os
import subprocess
import pytest


class TestRagImplementation:
    """Verify RAG demo implementation in LangChain."""

    REPO_DIR = "/workspace/langchain"

    # ------------------------------------------------------------------
    # L1: file existence & syntax
    # ------------------------------------------------------------------

    def test_rag_demo_exists(self):
        """examples/rag_demo.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "rag_demo.py")
        assert os.path.isfile(fpath), "rag_demo.py not found"

    def test_rag_demo_compiles(self):
        """rag_demo.py must compile."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "examples/rag_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: content & structure verification
    # ------------------------------------------------------------------

    def _read_source(self):
        fpath = os.path.join(self.REPO_DIR, "examples", "rag_demo.py")
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()

    def test_document_loading(self):
        """Demo must include document loading logic."""
        source = self._read_source()
        load_patterns = [
            "load",
            "read",
            "Document",
            "TextLoader",
            "DirectoryLoader",
            "open(",
        ]
        found = sum(1 for p in load_patterns if p in source)
        assert found >= 2, "Document loading not implemented"

    def test_text_splitting(self):
        """Demo must include text splitting/chunking."""
        source = self._read_source()
        split_patterns = [
            "split",
            "chunk",
            "TextSplitter",
            "RecursiveCharacterTextSplitter",
        ]
        found = any(p in source for p in split_patterns)
        assert found, "Text splitting not implemented"

    def test_vector_store(self):
        """Demo must configure a vector store."""
        source = self._read_source()
        vs_patterns = [
            "FAISS",
            "Chroma",
            "vectorstore",
            "VectorStore",
            "from_documents",
            "from_texts",
            "embedding",
        ]
        found = sum(1 for p in vs_patterns if p in source)
        assert found >= 2, "Vector store not configured"

    def test_retrieval_chain(self):
        """Demo must implement retrieval + generation chain."""
        source = self._read_source()
        chain_patterns = [
            "chain",
            "retriev",
            "qa",
            "generate",
            "RetrievalQA",
            "invoke",
            "run",
        ]
        found = sum(1 for p in chain_patterns if p in source.lower())
        assert found >= 2, "Retrieval chain not implemented"

    def test_source_citation(self):
        """Demo output should include source citations/references."""
        source = self._read_source()
        cite_patterns = [
            "source",
            "citation",
            "reference",
            "metadata",
            "page_content",
            "document",
        ]
        found = sum(1 for p in cite_patterns if p in source.lower())
        assert found >= 2, "Source citation handling not implemented"

    def test_rag_demo_runs(self):
        """rag_demo.py must run and exit with code 0."""
        result = subprocess.run(
            ["python", "examples/rag_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"Demo failed:\n{result.stderr}"

    def test_output_has_content(self):
        """Demo must produce non-empty output."""
        result = subprocess.run(
            ["python", "examples/rag_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"Demo failed: {result.stderr[:500]}")
        assert len(result.stdout.strip()) > 10, "Demo output is too short"

    def test_config_file_if_exists(self):
        """If rag_config.yaml exists, it must be valid YAML."""
        fpath = os.path.join(self.REPO_DIR, "examples", "rag_config.yaml")
        if not os.path.isfile(fpath):
            pytest.skip("rag_config.yaml not created (optional)")
        import yaml

        with open(fpath, "r") as f:
            config = yaml.safe_load(f)
        assert isinstance(config, dict), "Config must be a YAML mapping"

    def test_no_external_api_required(self):
        """Demo should run locally without external API keys (mock LLM if needed)."""
        source = self._read_source()
        # Should use mock/fake LLM or local model
        local_patterns = [
            "mock",
            "fake",
            "FakeLLM",
            "local",
            "HuggingFace",
            "dummy",
            "test",
            "FakeListLLM",
        ]
        found = any(p.lower() in source.lower() for p in local_patterns)
        # If not found, the demo might still work with env var check
        if not found:
            # Check it doesn't hard-require OPENAI_API_KEY without fallback
            assert (
                "OPENAI_API_KEY" not in source or "os.environ.get" in source
            ), "Demo appears to require external API key without fallback"
