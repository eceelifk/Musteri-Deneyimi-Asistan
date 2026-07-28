from sentence_transformers import CrossEncoder
from app.config import CROSS_ENCODER_MODEL_NAME

_cross_encoder_model = None

def get_cross_encoder():
    global _cross_encoder_model
    if _cross_encoder_model is None:
        print("Loading Cross-Encoder model for re-ranking...")
        # Use CPU by default if GPU is not easily available, or let sentence_transformers handle it
        _cross_encoder_model = CrossEncoder(CROSS_ENCODER_MODEL_NAME)
        print("Cross-Encoder loaded successfully!")
    return _cross_encoder_model

def rerank_documents(query: str, documents: list[dict], top_k: int = 3) -> list[dict]:
    """
    Reranks a list of retrieved documents based on the exact query using a Cross-Encoder.
    Documents should be a list of dicts, where each dict has at least a "chunk" key.
    """
    if not documents:
        return []

    model = get_cross_encoder()
    
    # Create pairs of (query, document_text)
    pairs = [[query, doc["chunk"]] for doc in documents]
    
    # Predict scores
    scores = model.predict(pairs)
    
    # Attach scores to documents
    for i, doc in enumerate(documents):
        # We override the bi-encoder score with the more accurate cross-encoder score
        doc["score"] = float(scores[i])
        
    # Sort by new cross-encoder score descending
    documents.sort(key=lambda x: x["score"], reverse=True)
    
    # Filter out irrelevant documents (Cross-Encoder score < 0.0)
    # This prevents hallucination when the user asks about a product not in the DB
    filtered_docs = [doc for doc in documents if doc["score"] > 0.0]
    
    return filtered_docs[:top_k]
