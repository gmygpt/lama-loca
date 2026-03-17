"""
LLM Engine — мощная обёртка над llama-cpp-python
Поддержка chat-формата, streaming, продвинутый sampling
"""
import os
from typing import Generator, Optional

from rich.console import Console

import config

console = Console()


class LLMEngine:
    """Обёртка над локальной LLM с максимальной производительностью"""

    def __init__(self, model_path: str = None):
        self.model_path = model_path or config.LLM_MODEL_PATH
        self.model = None
        self._loaded = False

    def load(self) -> bool:
        """Загрузить модель"""
        from llama_cpp import Llama

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Модель не найдена: {self.model_path}\n"
                f"Скачайте модель и поместите как models/model.gguf\n"
                f"Рекомендуемые модели:\n"
                f"  - Qwen2.5-14B-Instruct-GGUF (Q4_K_M) — лучшее качество\n"
                f"  - Qwen2.5-7B-Instruct-GGUF (Q4_K_M) — баланс\n"
                f"  - Qwen2.5-32B-Instruct-GGUF (Q4_K_M) — максимум (нужно 20+ GB RAM)"
            )

        console.print(f"[yellow]Загрузка модели: {os.path.basename(self.model_path)}...[/yellow]")

        kwargs = {
            "model_path": self.model_path,
            "n_ctx": config.LLM_CONTEXT_SIZE,
            "n_gpu_layers": config.LLM_GPU_LAYERS,
            "n_batch": config.LLM_N_BATCH,
            "verbose": False,
        }

        if config.LLM_N_THREADS is not None:
            kwargs["n_threads"] = config.LLM_N_THREADS

        self.model = Llama(**kwargs)
        self._loaded = True
        console.print("[green]Модель загружена![/green]")
        return True

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def generate(self, prompt: str, max_tokens: int = None,
                 temperature: float = None) -> str:
        """Генерация текста"""
        if not self._loaded:
            self.load()

        max_tokens = max_tokens or config.LLM_MAX_TOKENS
        temperature = temperature if temperature is not None else config.LLM_TEMPERATURE

        response = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=config.LLM_TOP_P,
            repeat_penalty=config.LLM_REPEAT_PENALTY,
            stop=["<|im_end|>", "<|end|>", "</s>", "<|eot_id|>"],
            echo=False,
        )

        return response["choices"][0]["text"].strip()

    def generate_stream(self, prompt: str, max_tokens: int = None,
                        temperature: float = None) -> Generator[str, None, None]:
        """Потоковая генерация текста (для GUI)"""
        if not self._loaded:
            self.load()

        max_tokens = max_tokens or config.LLM_MAX_TOKENS
        temperature = temperature if temperature is not None else config.LLM_TEMPERATURE

        stream = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=config.LLM_TOP_P,
            repeat_penalty=config.LLM_REPEAT_PENALTY,
            stop=["<|im_end|>", "<|end|>", "</s>", "<|eot_id|>"],
            echo=False,
            stream=True,
        )

        for chunk in stream:
            token = chunk["choices"][0]["text"]
            if token:
                yield token

    def generate_with_context(self, template: str, topic: str, context: str,
                               max_tokens: int = None, stream: bool = False):
        """Генерация с контекстом из базы знаний"""
        prompt = template.format(
            system=config.SYSTEM_PROMPT,
            topic=topic,
            context=context,
        )

        if stream:
            return self.generate_stream(prompt, max_tokens=max_tokens)
        return self.generate(prompt, max_tokens=max_tokens)

    def get_model_info(self) -> dict:
        """Информация о загруженной модели"""
        if not self._loaded:
            return {"status": "не загружена", "path": self.model_path}

        return {
            "status": "загружена",
            "path": os.path.basename(self.model_path),
            "context_size": config.LLM_CONTEXT_SIZE,
            "gpu_layers": config.LLM_GPU_LAYERS,
        }
