"""
Vector DB + Retrieval Chain — embeds facts from a FactsLedger and
stores them in Chroma so they can be searched by MEANING, not just
exact keyword matches. This lets Day 4's router correctly match a
job requirement like "stakeholder management" against a resume fact
like "worked closely with clients" even though the wording differs.
"""

import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.schemas.facts import FactsLedger, Fact

# A small, fast, free, locally-run embedding model. No API key needed —
# this downloads once and runs entirely on your machine.
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_embeddings = None  # lazy-loaded so we don't reload the model every call


def get_embeddings_model():
    """Loads the embedding model once and reuses it, since loading
    is somewhat slow and we don't want to repeat it unnecessarily."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embeddings


def facts_to_documents(ledger: FactsLedger) -> list[Document]:
    """Converts each Fact into a LangChain Document — the standard
    unit Chroma expects. We keep the fact's metadata (id, type,
    source_line) attached so we can trace back to it later, exactly
    like Day 1's traceability requirement demands."""
    documents = []
    for fact in ledger.facts:
        documents.append(
            Document(
                page_content=fact.content,
                metadata={
                    "fact_id": fact.fact_id,
                    "fact_type": fact.fact_type.value,
                    "source_line": fact.source_line,
                    "resume_id": ledger.resume_id,
                },
            )
        )
    return documents


def build_vector_store(ledger: FactsLedger, persist_directory: str = ".chroma") -> Chroma:
    """Builds (or rebuilds) a Chroma vector store from a FactsLedger.
    Each resume gets its own collection, named after its resume_id,
    so facts from different resumes don't get mixed together."""
    documents = facts_to_documents(ledger)
    embeddings = get_embeddings_model()

    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=f"resume_{ledger.resume_id}",
        persist_directory=persist_directory,
    )
    return vector_store


def retrieve_relevant_facts(vector_store: Chroma, query: str, k: int = 5) -> list[Document]:
    """Given a query (e.g. a job requirement like 'stakeholder management'),
    returns the top-k most semantically similar facts from the vector store.
    This is meaning-based search: it will match related concepts even when
    the exact words differ."""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    results = vector_store.similarity_search(query, k=k)
    return results