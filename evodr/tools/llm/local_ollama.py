

"""
- Please install following Python packages:
    1. ollama
    2. langchain_ollama
    3. langchain
"""
from langchain_ollama import OllamaLLM
from typing import Any
from ...base import LLM


class LocalOllamaLLM(LLM):
    def __init__(self, model_name: str, **ollama_llm_init_params):
        """Deploy Ollama model on local devices.
        Args:
            model_name            : name of local Ollama model checkpoint.
            ollama_llm_init_params: initialization params for `langchain_ollama.OllamaLLM`.
        """
        super().__init__()
        self.model = OllamaLLM(model=model_name, **ollama_llm_init_params)

    def draw_sample(self, prompt: str | Any, *args, **kwargs) -> str:
        response = self.model.invoke(prompt)
        return response


if __name__ == '__main__':
    model = LocalOllamaLLM('qwen3:14b')
    print(model.draw_sample('hello'))