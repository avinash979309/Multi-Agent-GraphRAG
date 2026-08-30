from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
import os

from dotenv import load_dotenv
load_dotenv(".env")

# llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
# llm = ChatOpenAI()

# --- PHASE 1: Hugging Face LLM Integration ---
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

hf_token = os.environ.get("HF_TOKEN", "")
os.environ["HUGGINGFACEHUB_API_TOKEN"] = hf_token

hf_endpoint = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    task="text-generation",
    max_new_tokens=1024,
    temperature=0.1,
)
llm = ChatHuggingFace(llm=hf_endpoint)
# ---------------------------------------------

# llm = ChatGroq(
#     model="llama-3.1-70b-versatile",
#     temperature=0,
#     max_tokens=None,
#     timeout=None,
#     max_retries=2,
#     # other params...
# )