import os
from utils.helpers import setup_logger

logger = setup_logger("OCRReader")

# Common Tesseract install path on Windows
_TESSERACT_DEFAULT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class OCRReader:
    def __init__(self, tesseract_cmd: str = None):
        self._available = False
        self._setup_tesseract(tesseract_cmd)

    def _setup_tesseract(self, tesseract_cmd: str):
        """Configure pytesseract if Tesseract is installed; degrade gracefully if not."""
        try:
            import pytesseract

            # Use provided path, or auto-detect on Windows
            cmd = tesseract_cmd or (
                _TESSERACT_DEFAULT if os.path.exists(_TESSERACT_DEFAULT) else None
            )
            if cmd:
                pytesseract.pytesseract.tesseract_cmd = cmd

            # Quick availability test
            pytesseract.get_tesseract_version()
            self._available = True
            logger.info("Tesseract OCR is available.")
        except ImportError:
            logger.warning("pytesseract not installed. OCR features will be disabled.")
        except Exception as e:
            logger.warning(
                f"Tesseract not found or not configured ({e}). "
                "OCR features disabled. Install from: https://github.com/UB-Mannheim/tesseract/wiki"
            )

    def extract_text(self, image_path: str) -> str:
        """Extract all text from an image. Returns empty string if OCR is unavailable."""
        if not self._available:
            return ""
        try:
            import pytesseract
            from PIL import Image

            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            logger.info(f"OCR extracted {len(text)} characters.")
            return text.strip()
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return ""

    def find_text_coordinates(self, image_path: str, target_text: str):
        """Find the screen coordinates of a specific text substring. Returns (x, y) or None."""
        if not self._available:
            return None
        try:
            import pytesseract
            from PIL import Image

            image = Image.open(image_path)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            target = target_text.lower()

            for i, word in enumerate(data["text"]):
                if target in word.lower():
                    x = data["left"][i]
                    y = data["top"][i]
                    w = data["width"][i]
                    h = data["height"][i]
                    return (x + w // 2, y + h // 2)

            return None
        except Exception as e:
            logger.error(f"OCR coordinate search error: {e}")
            return None
