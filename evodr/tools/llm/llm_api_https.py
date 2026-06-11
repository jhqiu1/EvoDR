
from __future__ import annotations

import requests
import json
from typing import Any

from evodr.base import LLM


class OpenAIAPI(LLM):
    def __init__(self, base_url: str, api_key: str, model: str, timeout=60, **kwargs):
        super().__init__()
        self._base_url = base_url
        self._key = api_key
        self._model = model
        self._timeout = timeout

    def draw_sample(self, prompt: str | Any, *args, **kwargs) -> str:
        messages = [{'role': 'user', 'content': prompt.strip()}] if isinstance(prompt, str) else prompt
        payload = {
            'model': self._model,
            'messages': messages,
            'stream': False,
        }
        headers = {
            'Authorization': f'Bearer {self._key}',
            'Content-Type': 'application/json',
        }
        response = requests.post(
            f'{self._base_url}/chat/completions',
            headers=headers,
            json=payload,
            timeout=self._timeout,
        )
        return response.json()['choices'][0]['message']['content']
