
from __future__ import annotations

import openai
from typing import Any

from evodr.base import LLM


class OpenAIAPI(LLM):
    def __init__(self, base_url: str, api_key: str, model: str, timeout=60, **kwargs):
        super().__init__()
        self._model = model
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, **kwargs)
        
        # Role descriptions for different expert roles
        self.role_description_A = 'You are an algorithm expert who is well versed in programming and algorithms, you are required to design algorithms and provide the corresponding code according to the proposed requirements.'
        self.role_description_S = "You, as an expert in the field of dynamic shop floor scheduling, need to evaluate heuristic rules in terms of minimizing the tardiness in a scenario where orders arrive dynamically."

    def draw_sample(self, prompt: str | Any, *args, **kwargs) -> str:
        if isinstance(prompt, str):
            prompt = [{'role': 'user', 'content': prompt.strip()}]
        response = self._client.chat.completions.create(
            model=self._model,
            messages=prompt,
            stream=False,
        )
        return response.choices[0].message.content
    
    def llm_A(self, text_input, temperature=1.0):
        """LLM as Algorithm Expert (A role)."""
        messages = [
            {"role": "system", "content": self.role_description_A},
            {"role": "user", "content": text_input}
        ]
        
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            extra_body={"thinking": {"type": "disabled"}}
        )

        usage_info = {
            'prompt_tokens': completion.usage.prompt_tokens,
            'completion_tokens': completion.usage.completion_tokens,
            'total_tokens': completion.usage.total_tokens
        }

        return completion.choices[0].message.content, usage_info

    def llm_S(self, text_input, temperature=1.0):
        """LLM as Scheduling Expert (S role)."""
        messages = [
            {"role": "system", "content": self.role_description_S},
            {"role": "user", "content": text_input}
        ]

        completion = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            extra_body={"thinking": {"type": "disabled"}}
        )

        usage_info = {
            'prompt_tokens': completion.usage.prompt_tokens,
            'completion_tokens': completion.usage.completion_tokens,
            'total_tokens': completion.usage.total_tokens
        }

        return completion.choices[0].message.content, usage_info
