import os
import mss
import mss.tools
from utils.helpers import setup_logger

logger = setup_logger("ScreenCapture")

# Common Tesseract install paths on Windows (used by OCRReader, but kept here as reference)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_TEMP_DIR = os.path.join(_BASE_DIR, "temp")


class ScreenCapture:
    def __init__(self, temp_dir: str = None):
        # Always use an absolute path so it works regardless of cwd
        self.temp_dir = temp_dir or _DEFAULT_TEMP_DIR
        os.makedirs(self.temp_dir, exist_ok=True)

    def capture(self, filename: str = "screenshot.png") -> str:
        """Capture the primary monitor and save to temp dir. Returns the saved file path."""
        filepath = os.path.join(self.temp_dir, filename)
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]   # Primary monitor
                sct_img = sct.grab(monitor)
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=filepath)
                logger.info(f"Screenshot saved: {filepath}")
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
        return filepath

    def find_template(self, template_path: str, screenshot_path: str, threshold: float = 0.8):
        """
        Find a UI element (template image) on a screenshot using OpenCV template matching.
        Returns (cx, cy) center coordinates of the first match, or None.
        """
        try:
            import cv2
            import numpy as np

            img_rgb = cv2.imread(screenshot_path)
            if img_rgb is None:
                logger.error(f"Could not read screenshot: {screenshot_path}")
                return None
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                logger.error(f"Could not read template: {template_path}")
                return None

            h, w = template.shape
            res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)

            for pt in zip(*loc[::-1]):
                return (pt[0] + w // 2, pt[1] + h // 2)

            return None
        except ImportError:
            logger.warning("opencv-python not installed. Template matching unavailable.")
            return None
        except Exception as e:
            logger.error(f"Template matching error: {e}")
            return None
