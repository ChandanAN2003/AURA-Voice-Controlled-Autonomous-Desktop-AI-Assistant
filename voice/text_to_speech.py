import pyttsx3
import threading
import queue
import time
import os
import tempfile
import asyncio
from utils.helpers import setup_logger

logger = setup_logger("TextToSpeech")

# Attempt importing advanced TTS components
try:
    import edge_tts
    import pygame
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.warning("edge-tts or pygame not found. Falling back to pyttsx3 exclusively. Run: pip install edge-tts pygame")

class TextToSpeech:
    def __init__(self):
        self.message_queue = queue.Queue()
        self.engine = None
        self._init_pyttsx3()
        
        # Start the background worker thread for TTS processing
        self.worker_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.worker_thread.start()

    def _init_pyttsx3(self):
        """Initialize the fallback offline engine on the main/worker thread."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 170)
            self.engine.setProperty('volume', 0.9)
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3 fallback: {e}")

    def speak(self, text: str):
        """Add text to the speaking queue."""
        logger.info(f"Queued to speak: {text}")
        self.message_queue.put(text)

    def _tts_worker(self):
        """Processes the TTS queue one by one to prevent threading crashes and overlaps."""
        while True:
            text = self.message_queue.get()
            if text is None:
                break
                
            success = False
            if EDGE_TTS_AVAILABLE:
                success = self._speak_edge(text)
                
            # Fallback to local offline TTS if Edge fails or unavailable
            if not success and self.engine is not None:
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    logger.error(f"Pyttsx3 fallback error: {e}")
                    
            self.message_queue.task_done()

    def _speak_edge(self, text: str) -> bool:
        """Play TTS using Microsoft Edge's Neural voices."""
        try:
            # Create a temporary file for the MP3 chunk
            temp_path = tempfile.mktemp(suffix=".mp3")
            
            # Use 'en-US-AriaNeural' for a very natural, high-quality voice
            voice = "en-US-AriaNeural"
            
            async def generate_audio():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(temp_path)
            
            asyncio.run(generate_audio())
            
            # Start initialized pygame mixer
            if not pygame.mixer.get_init():
                pygame.mixer.init()
                
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            # Wait for audio to finish explicitly
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            pygame.mixer.music.unload()
            
            # Clean up temp file safely
            try:
                os.remove(temp_path)
            except Exception:
                pass
            return True
        except Exception as e:
            logger.warning(f"Edge TTS failed (maybe no internet?), falling back offline. Error: {e}")
            return False
