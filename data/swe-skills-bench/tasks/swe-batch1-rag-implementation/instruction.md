# SWE-Skills-Bench: rag-implementation (batch1)

# Task: Implement End-to-End RAG Demo in LangChain

## Background
   Create an end-to-end RAG (Retrieval-Augmented Generation) demonstration
   in LangChain showing data import, retriever configuration, and generation.

## Files to Create/Modify
   - examples/rag_demo.py (new)
   - examples/rag_config.yaml (configuration)
   - demo/rag/ (optional directory)

## Requirements
   
   RAG Pipeline Components:
   1) Data Import:
      - Load documents from local files
      - Text splitting with configurable chunk size
   
   2) Retriever Configuration:
      - Vector store setup (FAISS or Chroma)
      - Embedding model configuration
      - Similarity search parameters
   
   3) Generation Pipeline:
      - Retrieval + LLM chain
      - Context injection into prompt
      - Source citation in output
   
   Minimal Local Configuration:
   - Can run without external API (mock LLM if needed)
   - README with clear instructions

4. Output Requirements:
   - Generated output includes retrieved context
   - Source references present in output
   - Successful exit code

## Acceptance Criteria
   - `python examples/rag_demo.py` exits with code 0
   - Output contains retrieved context snippets
   - Source citations or references present
