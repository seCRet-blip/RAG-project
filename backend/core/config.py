"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "documents"

    vllm_base_url: str = "http://localhost:8002/v1"
    vllm_model: str = "Qwen/Qwen2.5-0.5B-Instruct"

    api_base_url: str = "http://127.0.0.1:8000"
    frontend_port: int = 8788

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 5

    # Small vLLM budget (Qwen 0.5B --max-model-len 2048)
    rag_top_k: int = 3
    rag_max_context_chars: int = 2800
    rag_max_chunk_chars: int = 700
    rag_max_output_tokens: int = 160

    crawl_max_pages: int = 100
    crawl_delay_seconds: float = 1.0
