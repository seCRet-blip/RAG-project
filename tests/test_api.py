"""API route tests."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.rag.pipeline import RAGResult

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "qdrant" in data
    assert "vllm" in data


def test_chat_endpoint_structure():
    mock_result = RAGResult(answer="Test answer", chunks=[])

    with patch("backend.api.routes.chat.RAGPipeline") as mock_pipeline:
        instance = mock_pipeline.return_value
        instance.run = AsyncMock(return_value=mock_result)
        response = client.post("/chat/", json={"message": "What is a pod?"})

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Test answer"
    assert data["sources"] == []
