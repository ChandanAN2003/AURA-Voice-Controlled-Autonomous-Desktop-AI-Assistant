import json
import queue
import sys
import threading
import time
import os
import urllib.request
import zipfile
import shutil
import sounddevice as sd
from utils.helpers import setup_logger

logger = setup_logger("SpeechToText")

class SpeechToText:
    def __init__(self, model_path="voice/vosk_model"):
        self.model_path = model_path
        self.q = queue.Queue()
        self.model = None

    def _load_model(self):
        """Lazy-load the Vosk model. Auto-downloads if missing."""
        if self.model:
            return True
        
        if not os.path.exists(self.model_path):
            logger.info("Vosk model not found. Downloading 'vosk-model-small-en-us-0.15' (approx 40MB)...")
            try:
                os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
                url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
                zip_path = os.path.join(os.path.dirname(self.model_path), "vosk_model.zip")
                urllib.request.urlretrieve(url, zip_path)
                logger.info("Download complete. Extracting...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(os.path.dirname(self.model_path))
                os.remove(zip_path)
                # The extracted folder is named 'vosk-model-small-en-us-0.15'
                extracted_folder = os.path.join(os.path.dirname(self.model_path), "vosk-model-small-en-us-0.15")
                if os.path.exists(extracted_folder):
                    time.sleep(1) # wait for antivirus to finish scanning
                    shutil.move(extracted_folder, self.model_path)
                logger.info("Vosk model downloaded and extracted successfully.")
            except Exception as e:
                logger.error(f"Failed to download or extract model: {e}")
                return False

        try:
            from vosk import Model
            self.model = Model(self.model_path)
            logger.info("Vosk model loaded successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            return False

    def callback(self, indata, frames, time_info, status):
        """Called for each audio block from sounddevice."""
        if status:
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))

    def listen(self, timeout=7) -> str:
        """Listen for speech and return recognized text. Stops after timeout seconds."""
        try:
            if not self._load_model():
                return "Error: Vosk model not found. Please download it to voice/vosk_model folder."

            from vosk import KaldiRecognizer
            recognizer = KaldiRecognizer(self.model, 16000)
            logger.info("Listening for speech...")

            result_text = ""
            end_time = time.time() + timeout

            try:
                # Try with explicit channels=1 first
                stream = sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                           channels=1, callback=self.callback)
            except Exception as first_e:
                logger.warning(f"Failed to open mic with channels=1 ({first_e}). Trying default...")
                # Fallback to whatever the system default allows
                stream = sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                           callback=self.callback)

            with stream:
                while time.time() < end_time:
                    try:
                        data = self.q.get(timeout=1)
                    except queue.Empty:
                        continue

                    if recognizer.AcceptWaveform(data):
                        res = json.loads(recognizer.Result())
                        text = res.get("text", "").strip()
                        if text:
                            logger.info(f"Heard: {text}")
                            result_text = text
                            break

            if not result_text:
                # Check partial result
                partial = json.loads(recognizer.FinalResult())
                result_text = partial.get("text", "").strip()

            return result_text

        except Exception as e:
            logger.error(f"Error during speech recognition: {e}")
            return ""
