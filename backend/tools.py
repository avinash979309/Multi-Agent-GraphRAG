from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
import operator
from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langgraph.prebuilt import ToolNode
import os
import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
# from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEndpointEmbeddings
import pickle
import base64, io, os, sys
import matplotlib


matplotlib.use("Agg")
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup


from dotenv import load_dotenv
load_dotenv(".env")

"""
We are defining some tools
We will also define some more tools that our agents will use in the future
"""

repl = (
    PythonREPL()
)  # Warning: This executes code locally, which can be unsafe when not sandboxed

search = DuckDuckGoSearchResults(output_format="list")
# print(search.invoke("last week sensex closing price"))

# Default vector database
# def create_vector_db(embeddings=OpenAIEmbeddings()):
def create_vector_db(embeddings=HuggingFaceEndpointEmbeddings(model="sentence-transformers/all-MiniLM-L6-v2")):
    try:
        # 1. Load the PDF file
        for files in os.listdir("./default_files"):
            if files.endswith(".pdf"):
                loader = PyPDFLoader(os.path.join("./default_files", files))
                documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.split_documents(documents)
        db = FAISS.from_documents(docs, embeddings)
        db.save_local("./default_vector_db")
        
        # --- PHASE 2: BM25 Pickling ---
        from langchain_community.retrievers import BM25Retriever
        bm25_retriever = BM25Retriever.from_documents(docs)
        bm25_retriever.k = 4
        with open("./default_bm25_retriever.pkl", "wb") as f:
            pickle.dump(bm25_retriever, f)
        # ------------------------------
                
    except Exception as e:
        print(f"Error loading PDF file: {e}")
        return None

create_vector_db()


@tool
def duckduckgo_search(query: Annotated[str, "The search query."]):
    """Use this tool to perform a search using DuckDuckGo and return the content of the search results."""
    search_tool = DuckDuckGoSearchResults(output_format="list")
    results = search_tool.invoke(query)
    contents = []

    for result in results:
        url = result["link"]
        try:
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            print(f"Retrieving content from: {url}")
            response = requests.get(
                url, timeout=10, headers=headers
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text()
            contents.append(
                {
                    "url": url,
                    "content": text[
                        :1000
                    ],  # Limit content to first 1000 characters for brevity
                }
            )
        except requests.RequestException as e:
            print(f"Failed to retrieve content: {e}")
            # contents.append({
            #     'url': url,
            #     'content': f"Failed to retrieve content: {e}"
            # })

    return "Search results:\n" + "\n".join(
        [f"{content['url']}\n{content['content']}\n" for content in contents]
    )


@tool
def python(
    code: Annotated[
        str, "The python code to execute. Don't show the plot in the output."
    ],
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""

    try:
        # Execute the code
        result = repl.run(code)

        # Check if a plot was generated
        if plt.get_fignums():
            # Ensure the generated_files directory exists
            os.makedirs("generated_files", exist_ok=True)
            # Save the plot to a file in the generated_files directory
            file_path = os.path.join("generated_files", "plot.png")
            plt.savefig(file_path)
            plt.close()
            result_str = f"Successfully executed:\n```python\n{code}\n```\nPlot saved to: {file_path}"
        else:
            result_str = (
                f"Successfully executed:\n```python\n{code}\n```\nOutput: {result}"
            )

    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"

    return result_str


@tool
def retrieve_documents(query: str):
    """Searches for documents related to a given query."""
    try:
        # --- PHASE 2: Hybrid Search with RRF ---
        # db = FAISS.load_local("./default_vector_db", OpenAIEmbeddings(), allow_dangerous_deserialization=True)
        # retriever = db.as_retriever()
        db = FAISS.load_local(
            "./default_vector_db", 
            HuggingFaceEndpointEmbeddings(model="sentence-transformers/all-MiniLM-L6-v2"), 
            allow_dangerous_deserialization=True
        )
        faiss_retriever = db.as_retriever(search_kwargs={"k": 5})
        
        try:
            with open("./default_bm25_retriever.pkl", "rb") as f:
                bm25_retriever = pickle.load(f)
        except:
            bm25_retriever = None

        if faiss_retriever is None:
            return "Retriever is not initialized."
            
        try:
            faiss_docs = faiss_retriever.invoke(query)
            bm25_docs = bm25_retriever.invoke(query) if bm25_retriever else []
            
            # Reciprocal Rank Fusion
            scores = {}
            for k, doc_list in enumerate([faiss_docs, bm25_docs]):
                for rank, doc in enumerate(doc_list):
                    doc_id = doc.page_content
                    scores[doc_id] = scores.get(doc_id, 0) + 1 / (60 + rank)
                    
            sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
            return [doc_content for doc_content, _ in sorted_docs]
        except Exception as e:
            return f"Failed to retrieve documents. Error: {repr(e)}"
        # ---------------------------------------
    except Exception as e:
        return f"Failed to load the vector database. Error: {repr(e)}"


@tool
def user_file_retriever_tool(query: str):
    """Searches for documents related to a given query on a user file."""
    # --- PHASE 2: Hybrid Search with RRF ---
    # db = FAISS.load_local("./vector_db", OpenAIEmbeddings(), allow_dangerous_deserialization=True)
    # retriever = db.as_retriever()
    db = FAISS.load_local("./vector_db", HuggingFaceEndpointEmbeddings(model="sentence-transformers/all-MiniLM-L6-v2"), allow_dangerous_deserialization=True)
    faiss_retriever = db.as_retriever(search_kwargs={"k": 5})
    
    try:
        with open("./bm25_retriever.pkl", "rb") as f:
            bm25_retriever = pickle.load(f)
    except:
        bm25_retriever = None

    if faiss_retriever is None:
        return "Retriever is not initialized."
        
    try:
        faiss_docs = faiss_retriever.invoke(query)
        bm25_docs = bm25_retriever.invoke(query) if bm25_retriever else []
        
        # Reciprocal Rank Fusion
        scores = {}
        for k, doc_list in enumerate([faiss_docs, bm25_docs]):
            for rank, doc in enumerate(doc_list):
                doc_id = doc.page_content
                scores[doc_id] = scores.get(doc_id, 0) + 1 / (60 + rank)
                
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
        return [doc_content for doc_content, _ in sorted_docs]
    except Exception as e:
        return f"Failed to retrieve documents. Error: {repr(e)}"
    # ---------------------------------------


# --- PHASE 3: Knowledge Graph Traversal Tool (GraphRAG) ---
import networkx as nx

@tool
def graph_traversal_tool(entity: str):
    """Searches the extracted Knowledge Graph for a specific financial entity and returns its relationships (e.g. subsidiaries, competitors, executives)."""
    try:
        with open("./knowledge_graph.pkl", "rb") as f:
            G = pickle.load(f)
    except:
        return "Knowledge Graph is not initialized. Please upload a PDF first."

    # Look for matching nodes (case-insensitive partial match)
    matches = [node for node in G.nodes if entity.lower() in str(node).lower()]
    
    if not matches:
        return f"No relationships found in the Knowledge Graph for entity: {entity}"
        
    results = []
    for match in matches:
        neighbors = G[match]
        for neighbor, edge_data in neighbors.items():
            rel = edge_data.get('relation', 'connected to')
            results.append(f"{match} --[{rel}]--> {neighbor}")
            
    return "Knowledge Graph Relationships:\n" + "\n".join(results)
# --------------------------------------------------------

@tool
def date_tool():
    """This tool will return the current date and time."""

    return f"The current date and time is {datetime.datetime.now()}"


tools = [
    python,
    retrieve_documents,
    date_tool,
    user_file_retriever_tool,
    duckduckgo_search,
    graph_traversal_tool, # Phase 3
]
tool_node = ToolNode(tools)
