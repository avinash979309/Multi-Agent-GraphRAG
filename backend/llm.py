from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
# llm = ChatOpenAI()

import os
import requests
from dotenv import load_dotenv
load_dotenv(".env")

from langchain_groq import ChatGroq

groq_api_key = os.environ.get("GROQ_API_KEY", "")
selected_model = "llama-3.3-70b-versatile" # default guess

try:
    if groq_api_key:
        res = requests.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {groq_api_key}"})
        if res.status_code == 200:
            models = res.json().get("data", [])
            if models:
                # Pick the best text model
                for m in models:
                    if "llama" in m["id"].lower() and "vision" not in m["id"].lower() and "tool-use" not in m["id"].lower() and "guard" not in m["id"].lower():
                        selected_model = m["id"]
                        break
except Exception:
    pass

llm = ChatGroq(
    model=selected_model,
    temperature=0,
    api_key=groq_api_key
)

# llm = ChatGroq(
#     model="llama-3.1-70b-versatile",
#     temperature=0,
#     max_tokens=None,
#     timeout=None,
#     max_retries=2,
#     # other params...
# )