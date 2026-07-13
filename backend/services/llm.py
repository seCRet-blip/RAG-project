"""vLLM OpenAI-compatible client (local, low VRAM)."""

from openai import AsyncOpenAI


class VLLMClient:
    def __init__(self, base_url: str, model: str, timeout: float = 120.0) -> None:
        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key="not-needed",
            timeout=timeout,
        )
        self._model = model

    async def generate(self, prompt: str, max_tokens: int = 256) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.2,
            )
        except Exception as exc:
            raise RuntimeError(
                f"vLLM not reachable at {self._client.base_url}. "
                "Start it with: docker compose --profile vllm up -d vllm"
            ) from exc

        return response.choices[0].message.content or ""

    async def health_check(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False
