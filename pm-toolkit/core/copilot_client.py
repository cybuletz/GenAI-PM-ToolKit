import requests
from typing import Union

GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com/chat/completions"


class CopilotClient:
    """
    Calls the GitHub Models REST API using the user's GitHub personal access token.
    Supports both plain text and multimodal (text + images) messages.
    """

    def __init__(self, token: str, model: str = "gpt-4o"):
        self.token = token
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        resp = requests.post(GITHUB_MODELS_ENDPOINT, headers=self.headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def complete_multimodal(self, system: str, content: list) -> str:
        """
        content: list of dicts, each either:
          {"type": "text", "text": "..."}
          {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
        }
        resp = requests.post(GITHUB_MODELS_ENDPOINT, headers=self.headers, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
