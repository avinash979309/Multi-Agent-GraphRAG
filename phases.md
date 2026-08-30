# Implementation Plan: HP3 Upgrades (3 Phases)

This document outlines the three-phase implementation strategy to integrate advanced GraphRAG features into the HP3 project. 

**Core Directives for Implementation:**
*   **Safe Modding:** All original code being modified will be commented out, rather than deleted. New code will be written alongside it. This ensures immediate rollback capability.
*   **OpenAI to Hugging Face Migration:** Since OpenAI API keys are unavailable, the system will be entirely migrated to utilize Hugging Face models for both Embeddings and LLM Generation.

---

## Phase 1: Foundation & LLM Migration
**Focus:** Replace OpenAI dependencies with Hugging Face and introduce the first LLM-based improvement.

1.  **Hugging Face Integration (`llm.py` & `online_data_process.py`):**
    *   Comment out OpenAI embeddings and LLM initializations.
    *   Implement Hugging Face Endpoint/Inference integrations for both the LLM and the Embeddings using the provided Hugging Face API key.
2.  **Pre-Retrieval Query Refinement (`workflow.py`):**
    *   Add a pre-processing node in the LangGraph workflow.
    *   This node will intercept the user's raw query and use the Hugging Face LLM to fix typos and expand domain-specific acronyms *before* vector retrieval begins.

## Phase 2: Enhanced Retrieval & Context Management
**Focus:** Upgrade how the system finds documents and how it remembers the conversation.

1.  **Hybrid Search with RRF (`tools.py` & `online_data_process.py`):**
    *   Implement a sparse BM25 keyword retriever to run in parallel with the dense FAISS vector retriever.
    *   Create a Reciprocal Rank Fusion (RRF) algorithm to mathematically merge and rank the results from both retrievers.
2.  **Intelligent Follow-up Detection (`workflow.py`):**
    *   Implement an LLM check to determine if the current query is a follow-up to the previous one (e.g., resolving pronouns).
    *   If detected as a follow-up, explicitly inject the retrieved context from the previous turn into the current search loop.

## Phase 3: Advanced Ingestion & Graph Architecture
**Focus:** Upgrade document parsing and introduce the GraphRAG concept.

1.  **Semantic Document Chunking (`online_data_process.py`):**
    *   Replace `RecursiveCharacterTextSplitter` with semantic parsing logic (e.g., chunking based on markdown headers, paragraphs, or logical boundaries).
2.  **Knowledge Graph Extraction (GraphRAG) (`online_data_process.py` & `tools.py`):**
    *   During PDF ingestion, use the LLM to extract key financial entities and their relationships.
    *   Build a lightweight in-memory graph using `NetworkX`.
    *   Provide the `Researcher` agent with a new tool to traverse this graph for complex relational queries.
