import mss
import base64
import requests
import json
import os
from io import BytesIO
from PIL import Image
from utils.helpers import setup_logger
from backend.config import OLLAMA_URL

logger = setup_logger("VisionAI")
VISION_MODEL = "llama3.2-vision"  # Needs to be pulled first via `ollama pull llama3.2-vision`

class ScreenAnalyzer:
    def __init__(self):
        self.url = OLLAMA_URL

    def capture_screen_base64(self) -> str:
        """Takes a full screen screenshot and returns a compressed base64 string."""
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                
                # Compress logic: Convert to JPEG, quality 50
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=50)
                b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                
                return b64
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return ""

    def analyze(self, query: str = "Describe what you see on my screen concisely.") -> str:
        """
        Takes a screenshot of the entire desktop and asks the vision model about it.
        """
        logger.info(f"Vision analyzing screen for: {query}")
        
        b64_img = self.capture_screen_base64()
        if not b64_img:
            return "Error: Could not capture the desktop screen."

        payload = {
            "model": VISION_MODEL,
            "prompt": query,
            "stream": False,
            "images": [b64_img]
        }

        try:
            logger.info("Sending screen to Ollama vision model...")
            resp = requests.post(self.url, json=payload, timeout=45)
            
            if resp.status_code == 200:
                answer = resp.json().get("response", "").strip()
                return answer
            elif resp.status_code == 404:
                return (f"Error: Vision model '{VISION_MODEL}' not found. "
                        f"Run: ollama pull {VISION_MODEL} in your terminal to enable Screen-Awareness.")
            else:
                return f"Error: Vision API Failed - {resp.status_code}"
                
        except requests.exceptions.ConnectionError:
            return "Error: Ollama server is offline."
        except requests.exceptions.Timeout:
            return "Error: Vision analysis timed out. The model is large and taking too long."
        except Exception as e:
            logger.error(f"Vision processing error: {e}")
            return f"Error: {e}"
