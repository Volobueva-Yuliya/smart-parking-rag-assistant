import pytest
from unittest.mock import MagicMock, patch
from stage_1.app.rag_pipeline import run_rag_pipeline

@patch("stage_1.app.rag_pipeline.weaviate.connect_to_local")
@patch("stage_1.app.rag_pipeline.get_embedding")
@patch("stage_1.app.rag_pipeline.ChatOpenAI")
@patch("stage_1.app.rag_pipeline.ChatPromptTemplate")
def test_run_rag_pipeline(mock_prompt_class, mock_llm_class, mock_get_emb, mock_weaviate, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    
    # Mock Weaviate
    mock_client = MagicMock()
    mock_weaviate.return_value = mock_client
    mock_collection = MagicMock()
    mock_client.collections.get.return_value = mock_collection
    
    mock_obj = MagicMock()
    mock_obj.properties = {"content": "The parking is open from 7 to 23."}
    mock_collection.query.near_vector.return_value.objects = [mock_obj]
    
    # Mock Embedding
    mock_get_emb.return_value = [0.1, 0.2]
    
    # Mock LLM and Chain
    mock_llm = MagicMock()
    mock_llm_class.return_value = mock_llm
    
    mock_prompt = MagicMock()
    mock_prompt_class.from_template.return_value = mock_prompt
    
    mock_chain = MagicMock()
    mock_prompt.__or__.return_value = mock_chain
    
    mock_chain.invoke.return_value = MagicMock(content="Open from 7:00 to 23:00.")
    
    result = run_rag_pipeline("What are the hours?")
    
    assert result == "Open from 7:00 to 23:00."
    mock_weaviate.assert_called_once()
    mock_chain.invoke.assert_called_once()

@patch("stage_1.app.rag_pipeline.weaviate.connect_to_local")
@patch("stage_1.app.rag_pipeline.get_embedding")
def test_run_rag_pipeline_no_results(mock_get_emb, mock_weaviate, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    
    mock_client = MagicMock()
    mock_weaviate.return_value = mock_client
    mock_collection = MagicMock()
    mock_client.collections.get.return_value = mock_collection
    mock_collection.query.near_vector.return_value.objects = []
    
    result = run_rag_pipeline("Some obscure question")
    assert result == "I do not have that information in the parking knowledge base."
