import requests
import json
from backend.config import GEMINI_API_KEY
from utils.helpers import setup_logger

logger = setup_logger("GeminiClient")


class GeminiClient:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = "gemini-1.5-flash"
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def is_available(self) -> bool:
        """Check if the Gemini API key is configured."""
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Generate text using Gemini 1.5 Flash.
        Guarantees JSON output if required.
        """
        if not self.is_available():
            logger.error("Gemini API key is not configured.")
            return "Error: Gemini API key is missing. Set GEMINI_API_KEY in your environment."

        try:
            # We append the key to the URL parameters to prevent exposing it in standard headers
            target_url = f"{self.url}?key={self.api_key}"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            }

            if system_prompt:
                payload["systemInstruction"] = {
                    "parts": [
                        {"text": system_prompt}
                    ]
                }

            # Force JSON response if requested
            if "json" in prompt.lower() or "json" in system_prompt.lower():
                payload["generationConfig"] = {
                    "responseMimeType": "application/json"
                }

            logger.info(f"Sending request to Gemini model '{self.model}'...")
            response = requests.post(target_url, json=payload, timeout=20)

            if response.status_code == 200:
                data = response.json()
                try:
                    reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    logger.info("Received response from Gemini successfully.")
                    return reply
                except (KeyError, IndexError, TypeError) as e:
                    logger.error(f"Failed to parse Gemini response structure: {data}")
                    return f"Error: Unexpected response structure from Gemini: {e}"
            else:
                logger.error(f"Gemini API Error: {response.status_code} - {response.text}")
                return f"Error: Gemini returned HTTP {response.status_code}"

        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Gemini API. Check your internet connection.")
            return "Error: Cannot connect to Gemini API. Please check your internet connection."
        except requests.exceptions.Timeout:
            logger.error("Gemini request timed out.")
            return "Error: Gemini request timed out."
        except Exception as e:
            logger.error(f"Unexpected error contacting Gemini: {e}")
            return f"Error: {e}"
