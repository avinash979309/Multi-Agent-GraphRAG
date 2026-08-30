from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
# from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

db = None

# --- PHASE 1: Hugging Face Embeddings Integration ---
# def create_retriever_from_pdf(filepath, embeddings=OpenAIEmbeddings()):
def create_retriever_from_pdf(filepath, embeddings=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")):
# ----------------------------------------------------
    """Creates a retriever tool from a PDF file."""
    try:
        # 1. Load the PDF file
        loader = PyPDFLoader(filepath)
        documents = loader.load()
    except Exception as e:
        print(f"Error loading PDF file: {e}")
        return None

    try:
        # 2. Split the text into chunks
        # text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        # docs = text_splitter.split_documents(documents)
        
        # --- PHASE 3: Semantic Document Chunking ---
        try:
            from langchain_experimental.text_splitter import SemanticChunker
            text_splitter = SemanticChunker(embeddings)
            docs = text_splitter.split_documents(documents)
        except ImportError:
            # Fallback to advanced logical/structural splitting if experimental is not installed
            text_splitter = RecursiveCharacterTextSplitter(
                separators=["\n\n", "\n", ".", "?", "!", " ", ""],
                chunk_size=1000, 
                chunk_overlap=200
            )
            docs = text_splitter.split_documents(documents)
        # ---------------------------------------------
    except Exception as e:
        print(f"Error splitting text: {e}")
        return None

    try:
        # 3. Create a FAISS vector store from the chunks and embeddings
        global db
        if not db:
            db = FAISS.from_documents(docs, embeddings)                    
        else:
            db.add_documents(docs)
            
        db.save_local("./vector_db")
        
        # --- PHASE 2: BM25 Keyword Retriever Creation ---
        import pickle
        from langchain_community.retrievers import BM25Retriever
        bm25_retriever = BM25Retriever.from_documents(docs)
        bm25_retriever.k = 4
        with open("./bm25_retriever.pkl", "wb") as f:
            pickle.dump(bm25_retriever, f)
        # ------------------------------------------------

        # --- PHASE 3: Knowledge Graph Extraction (GraphRAG) ---
        import networkx as nx
        from llm import llm
        
        G = nx.Graph()
        # For implementation speed, extract from a sample of top documents.
        for doc in docs[:5]:
            prompt = f"Extract financial entities and their relationships from this text as a list of triplets (Entity1, Relationship, Entity2). Text: {doc.page_content[:500]}\nOutput ONLY the triplets separated by newlines."
            try:
                response = llm.invoke(prompt)
                lines = response.content.split('\n')
                for line in lines:
                    parts = line.strip("()").split(",")
                    if len(parts) == 3:
                        e1, rel, e2 = [p.strip() for p in parts]
                        G.add_edge(e1, e2, relation=rel)
            except Exception as e:
                print(f"Graph extraction error: {e}")
                
        with open("./knowledge_graph.pkl", "wb") as f:
            pickle.dump(G, f)
        # ------------------------------------------------------

        retriever = db.as_retriever()

    except Exception as e:
        print(f"Error creating FAISS vector store: {e}")
        return None

    return retriever
