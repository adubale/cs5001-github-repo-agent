from dataclasses import dataclass
import requests

@dataclass
class OllamaLLM:
    model: str = "devstral-small-2:24b-cloud"
    host: str = "http://localhost:11434"
    temperature: float = 0.0
    timeout_s: int = 120

    def generate(self, prompt: str) -> str:
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": float(self.temperature)
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=self.timeout_s)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to call Ollama at {url}: {e}") from e

        data = response.json()
        return (data.get("response") or "").strip()