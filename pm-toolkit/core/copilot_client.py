import time
import requests
from typing import Union

GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com/chat/completions"

# Max characters of raw source text sent to the AI.
# GitHub Models free tier allows ~16k tokens total (system + user).
# System prompt is ~1200 tokens; leaving ~12k tokens for user text.
# At ~4 chars/token, 48000 chars is a safe ceiling.
MAX_RAW_TEXT_CHARS = 48_000


class CopilotClient:
    """
    Calls the GitHub Models REST API using the user's GitHub personal access token.
    Supports both plain text and multimodal (text + images) messages.
    Retries once on 429 after a short backoff.
    """

    def __init__(self, token: str, model: str = "gpt-4o"):
        self.token = token
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _post(self, payload: dict, timeout: int = 90, retries: int = 2) -> dict:
        for attempt in range(retries):
            resp = requests.post(
                GITHUB_MODELS_ENDPOINT,
                headers=self.headers,
                json=payload,
                timeout=timeout,
            )
            if resp.status_code == 429 and attempt < retries - 1:
                retry_after = int(resp.headers.get("Retry-After", 20))
                time.sleep(retry_after)
                continue
            resp.raise_for_status()
            return resp.json()
        resp.raise_for_status()  # final raise if all retries exhausted

    def complete(self, system: str, user: str) -> str:
        # Truncate source text to avoid exceeding token limits
        if len(user) > MAX_RAW_TEXT_CHARS:
            user = user[:MAX_RAW_TEXT_CHARS]
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        return self._post(payload)["choices"][0]["message"]["content"]

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
        return self._post(payload, timeout=120)["choices"][0]["message"]["content"]
