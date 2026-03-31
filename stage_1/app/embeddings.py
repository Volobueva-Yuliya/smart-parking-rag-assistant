from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Singleton instance of the model
_model = None
MODEL_NAME = "all-MiniLM-L6-v2"

def get_embedding_model():
    """
    Initialize the embedding model only once (Singleton).
    """
    global _model
    if _model is None:
        logger.info(f"Initializing embedding model: {MODEL_NAME}")
        # Importance of consistent embedding space:
        # Retrieval quality depends on identical embedding space. 
        # Using different models for ingestion and search breaks semantic search 
        # because different models map the same text to different vector coordinates.
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def get_embedding(text: str) -> list[float]:
    """
    Generate embedding for a given text using the shared model.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Input text must be a non-empty string.")

    stripped_text = text.strip()
    model = get_embedding_model()
    # Print the model name as a runtime check (during ingestion or search)
    # This confirms that the same model is used across the pipeline.
    # We use a logger here to keep it clean.
    
    # Use a robust encoding pattern: encode a list and return the first vector
    embedding = model.encode([stripped_text])[0]
    if isinstance(embedding, list):
        return embedding
    return embedding.tolist()
