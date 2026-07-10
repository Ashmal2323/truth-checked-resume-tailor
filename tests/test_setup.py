"""Sanity check: confirms venv, installed packages, and .env loading
all work together before we build anything real on top of them."""

import os
from dotenv import load_dotenv

def check_environment():
    load_dotenv()

    grok_key = os.getenv("GROK_API_KEY")
    langsmith_key = os.getenv("LANGCHAIN_API_KEY")

    print("Checking environment setup...")
    print(f"GROK_API_KEY loaded: {'YES' if grok_key else 'NO - .env not set up yet, that is expected right now'}")
    print(f"LANGCHAIN_API_KEY loaded: {'YES' if langsmith_key else 'NO - .env not set up yet, that is expected right now'}")

    import langchain
    import pydantic
    import chromadb
    import sentence_transformers
    print(f"LangChain version: {langchain.__version__}")
    print(f"Pydantic version: {pydantic.__version__}")
    print(f"ChromaDB version: {chromadb.__version__}")
    print("✅ All core libraries imported successfully.")

if __name__ == "__main__":
    check_environment()