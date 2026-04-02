import pytest
from unittest.mock import MagicMock, patch
from stage_1.app.embeddings import get_embedding, get_embedding_model
@patch("stage_1.app.embeddings.SentenceTransformer")
def test_get_embedding_model(mock_st):
    # Reset singleton for test
    import stage_1.app.embeddings
    stage_1.app.embeddings._model = None
    
    get_embedding_model()
    mock_st.assert_called_once_with("all-MiniLM-L6-v2")

@patch("stage_1.app.embeddings.get_embedding_model")
def test_get_embedding(mock_get_model):
    mock_model = MagicMock()
    mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
    mock_get_model.return_value = mock_model
    
    embedding = get_embedding("test text")
    assert embedding == [0.1, 0.2, 0.3]
    mock_model.encode.assert_called_once_with(["test text"])

def test_get_embedding_invalid_input():
    with pytest.raises(ValueError, match="Input text must be a non-empty string"):
        get_embedding("")
    with pytest.raises(ValueError, match="Input text must be a non-empty string"):
        get_embedding(None)
