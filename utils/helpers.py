import json
import logging
import re


def setup_logger(name: str) -> logging.Logger:
    """
    Create (or reuse) a named logger with a StreamHandler.
    Guards against adding duplicate handlers when modules are reloaded.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:          # Only add handler once
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s  [%(name)s]  %(levelname)s  %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def parse_json_safely(text: str) -> list:
    """
    Safely extract and parse a JSON array from LLM output.
    Handles:
      - Plain JSON arrays
      - JSON wrapped in ```json ... ``` markdown fences
      - JSON embedded somewhere inside a longer text
    Returns a list on success, [] on any failure.
    """
    if not text:
        return []

    # 1. Strip markdown fences
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()

    # 2. Try to parse directly
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return [result]
    except json.JSONDecodeError:
        pass

    # 3. Try to extract the first [...] array from the text
    match = re.search(r"\[.*?\]", text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    logging.getLogger("helpers").warning(f"Could not parse JSON from response: {text[:300]}")
    return []
