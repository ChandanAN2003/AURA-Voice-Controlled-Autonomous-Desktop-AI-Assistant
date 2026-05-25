import time
import threading
from datetime import datetime
from utils.helpers import setup_logger

logger = setup_logger("ProactiveAgent")

class ProactiveAgent:
    def __init__(self, tts_engine):
        self.tts_engine = tts_engine
        self.is_running = False
        self.thread = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            logger.info("Proactive Agent started.")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1)
        logger.info("Proactive Agent stopped.")

    def _run_loop(self):
        # Example: check every minute if it's 9:00 AM for a morning briefing
        while self.is_running:
            now = datetime.now()
            if now.hour == 9 and now.minute == 0:
                self.deliver_morning_briefing()
                # sleep to prevent triggering multiple times in the same minute
                time.sleep(60) 
            time.sleep(10)

    def deliver_morning_briefing(self):
        logger.info("Delivering morning briefing...")
        briefing = (
            "Good morning. The weather is currently clear and 24 degrees. "
            "You have 3 unread emails, and your first meeting is at 10 AM. "
            "Shall I set up your workspace?"
        )
        if self.tts_engine:
            self.tts_engine.speak_sync(briefing)
