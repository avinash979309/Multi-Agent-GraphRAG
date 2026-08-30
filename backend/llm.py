from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
# llm = ChatOpenAI()

import os

from dotenv import load_dotenv
load_dotenv(".env")

# --- PHASE 1: Groq LLM Integration (Free & Fast) ---
from langchain_groq import ChatGroq

groq_api_key = os.environ.get("GROQ_API_KEY", "")
llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0,
    api_key=groq_api_key
)
# ---------------------------------------------

# llm = ChatGroq(
#     model="llama-3.1-70b-versatile",
#     temperature=0,
#     max_tokens=None,
#     timeout=None,
#     max_retries=2,
#     # other params...
# )