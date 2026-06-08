# SWE-Skills-Bench: rag-implementation (batch2)

# Task: Create a RAG Demo Script for LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) is a framework for LLM applications. A new example script is needed that demonstrates an end-to-end Retrieval-Augmented Generation (RAG) pipeline — loading documents, building a vector index, performing semantic retrieval, and generating answers grounded in retrieved context.

## Files to Create

- `examples/rag_demo.py` — End-to-end RAG demonstration script

## Requirements

### Document Loading

- Load documents from a local source (text files, markdown, or inline sample data)
- Split documents into chunks of configurable size with overlap

### Vector Store

- Create an in-memory or local vector store from the document chunks
- Use an embedding model or function to convert text to vectors
- Support similarity search queries against the store

### Retrieval and Generation

- Given a user query, retrieve the top-k most relevant document chunks
- Construct a prompt that includes the retrieved context and the user question
- Generate an answer using an LLM interface (real or mock)
- Return the answer along with source references

### Configuration

- Chunk size, overlap, top-k, and model parameters must be configurable
- The script must have a `__main__` entry point for standalone execution

## Expected Functionality

- Running the script with a sample question produces an answer grounded in the loaded documents
- Retrieved chunks are relevant to the query
- Source references point back to the original document segments

## Acceptance Criteria

- The script loads source documents, chunks them, and builds a retrievable vector index over the chunked content.
- A user query triggers retrieval of the most relevant chunks before answer generation.
- The generated answer is explicitly grounded in the retrieved context rather than being returned without sources.
- The output includes both the answer and references to the retrieved source material.
- Retrieval settings such as chunk size, overlap, and top-k can be adjusted without rewriting the core pipeline.
