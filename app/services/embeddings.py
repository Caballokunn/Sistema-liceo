from functools import lru_cache

from app.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


# Los modelos E5 esperan los prefijos "passage: " (documentos) y "query: " (consultas).
def embed_passages(texts: list[str]) -> list[list[float]]:
    vectors = _model().encode(
        [f"passage: {t}" for t in texts],
        normalize_embeddings=True,
        batch_size=16,
        show_progress_bar=False,
    )
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    vector = _model().encode([f"query: {text}"], normalize_embeddings=True, show_progress_bar=False)[0]
    return vector.tolist()
