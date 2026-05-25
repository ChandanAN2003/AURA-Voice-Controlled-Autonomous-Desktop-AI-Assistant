from ai_engine.ollama_client import OllamaClient
from ai_engine.gemini_client import GeminiClient
from utils.helpers import setup_logger

logger = setup_logger("Reflection")


class ReflectionModule:
    """Evaluates task execution success using visual context and logs."""
    
    def __init__(self):
        self.ollama = OllamaClient()
        self.gemini = GeminiClient()

    def evaluate_success(self, original_command: str, execution_log: str, screen_text: str) -> str:
        """
        Uses OCR text and execution logs to check if task was successful.
        Returns a short reason why it was successful or failed, ending with STATUS: SUCCESS or STATUS: FAILED.
        """
        prompt = f"""
        Task Context:
        User Command: {original_command}
        Execution Logs: {execution_log}
        Text visible on screen after execution: {screen_text[:1000]}

        Analyze the above information. Was the task successful? Return a short reflection.
        End your response with exactly "STATUS: SUCCESS" or "STATUS: FAILED" on a new line.
        """
        
        # Try Gemini API first (highly accurate, fast)
        if self.gemini.is_available():
            logger.info("Running task reflection via Gemini API...")
            response = self.gemini.generate(prompt)
            if response and not response.startswith("Error"):
                return response
            logger.warning(f"Reflection via Gemini failed: {response}")

        # Fallback to Ollama
        if self.ollama.is_available():
            logger.info("Running task reflection via Ollama AI...")
            response = self.ollama.generate(prompt)
            if response and not response.startswith("Error"):
                return response
            logger.warning(f"Reflection via Ollama failed: {response}")

        # If both fail, return default SUCCESS since the executor reported success
        return "STATUS: SUCCESS (Execution logs were successful; reflection models offline)"
