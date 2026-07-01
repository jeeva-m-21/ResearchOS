from ...ports.embeddings import Embedder
from ...ports.llm import LLMProvider


class RecallService:
    """Ask/RAG: retrieve -> rerank -> generate -> cite (no citation, no claim)."""

    def __init__(self, llm: LLMProvider, embedder: Embedder) -> None:
        self.llm = llm
        self.embedder = embedder

    def ask(self, question: str) -> dict[str, object]:
        # TODO: hybrid retrieval over pgvector + grounded answer with block ids
        return {"answer": "", "citations": []}
