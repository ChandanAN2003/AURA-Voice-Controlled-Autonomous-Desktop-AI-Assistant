import base64
import requests
from utils.helpers import setup_logger

logger = setup_logger("VLMClient")

class VLMClient:
    """
    Client for interacting with Vision Language Models (like LLaVA) via Ollama.
    Allows AURA to 'see' and understand the content of screenshots.
    """
    def __init__(self, model: str = "llava", host: str = "http://127.0.0.1:11434"):
        self.model = model
        self.host = host

    def is_available(self) -> bool:
        try:
            res = requests.get(f"{self.host}/api/tags", timeout=2)
            if res.status_code == 200:
                models = [m.get("name") for m in res.json().get("models", [])]
                # Allow version tags like llava:latest
                return any(self.model in m for m in models)
            return False
        except requests.RequestException:
            return False

    def analyze_image(self, image_path: str, prompt: str = "Describe this image in detail.") -> str:
        """
        Send an image and prompt to the VLM.
        """
        if not self.is_available():
            logger.warning(f"VLM model '{self.model}' is not available in Ollama.")
            return "Vision Language Model is not currently available."

        try:
            with open(image_path, "rb") as image_file:
                image_b64 = base64.b64encode(image_file.read()).decode("utf-8")

            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False
            }
            logger.info(f"Sending image to {self.model} with prompt: {prompt}")
            response = requests.post(f"{self.host}/api/generate", json=payload, timeout=60)
            
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            else:
                logger.error(f"VLM API returned status {response.status_code}")
                return "Failed to analyze image."
        except Exception as e:
            logger.error(f"Error during VLM analysis: {e}")
            return f"Error: {e}"
