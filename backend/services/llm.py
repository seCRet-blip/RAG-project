"""vLLM OpenAI-compatible client (local, low VRAM)."""

from openai import APIConnectionError, APIStatusError, AsyncOpenAI, BadRequestError


class VLLMClient:
    def __init__(self, base_url: str, model: str, timeout: float = 120.0) -> None:
        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key="not-needed",
            timeout=timeout,
        )
        self._model = model

    async def generate(self, prompt: str, max_tokens: int = 160) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.2,
            )
        except BadRequestError as exc:
            raise RuntimeError(
                f"vLLM rejected the prompt (often context too long for 2048-token model): {exc}"
            ) from exc
        except APIConnectionError as exc:
            raise RuntimeError(
                f"vLLM not reachable at {self._client.base_url}. "
                "Start the local vLLM service (rag-vllm on port 8002)."
            ) from exc
        except APIStatusError as exc:
            raise RuntimeError(f"vLLM error {exc.status_code}: {exc.message}") from exc

        return response.choices[0].message.content or ""

    async def health_check(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False
