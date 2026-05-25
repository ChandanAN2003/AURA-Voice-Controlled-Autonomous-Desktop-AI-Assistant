import requests
import json
from backend.config import OLLAMA_URL, MODEL_NAME
from utils.helpers import setup_logger

logger = setup_logger("OllamaClient")


class OllamaClient:
    def __init__(self):
        self.url = OLLAMA_URL
        self.model = MODEL_NAME

    def is_available(self) -> bool:
        """Check if the Ollama server is reachable."""
        try:
            # Ping the Ollama tags endpoint
            base = self.url.replace("/api/generate", "")
            resp = requests.get(f"{base}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Generate text using the configured model via Ollama.
        Returns the response string, or an 'Error: ...' string on failure.
        """
        try:
            full_prompt = (
                f"{system_prompt}\n\nUser: {prompt}\nAI:"
                if system_prompt
                else prompt
            )
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False
            }

            logger.info(f"Sending request to Ollama model '{self.model}'...")
            response = requests.post(self.url, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                reply = data.get("response", "").strip()
                logger.info("Received response from Ollama successfully.")
                return reply
            elif response.status_code == 404:
                logger.error(f"Model '{self.model}' not found in Ollama. Pull it with: ollama pull {self.model}")
                return f"Error: Model '{self.model}' not found. Run: ollama pull {self.model}"
            else:
                logger.error(f"Ollama API Error: {response.status_code} - {response.text}")
                return f"Error: Ollama returned HTTP {response.status_code}"

        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama. Make sure Ollama is running: ollama serve")
            return "Error: Cannot connect to Ollama server. Please run 'ollama serve' first."
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out after 90 seconds.")
            return "Error: Ollama request timed out. The model may be loading – please try again."
        except Exception as e:
            logger.error(f"Unexpected error contacting Ollama: {e}")
            return f"Error: {e}"
