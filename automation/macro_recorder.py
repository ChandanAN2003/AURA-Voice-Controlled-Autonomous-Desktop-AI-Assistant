import json
import os
import time
import threading
from pynput import mouse, keyboard
from utils.helpers import setup_logger

logger = setup_logger("MacroRecorder")

class MacroRecorder:
    def __init__(self):
        self.macro_file = os.path.join(os.path.dirname(__file__), "macros.json")
        self.recording = []
        self.is_recording = False
        self.start_time = 0
        self.current_macro_name = ""

        # Load existing
        self.macros = {}
        if os.path.exists(self.macro_file):
            try:
                with open(self.macro_file, "r") as f:
                    self.macros = json.load(f)
            except Exception as e:
                logger.error(f"Error loading macros: {e}")

    def on_press(self, key):
        if not self.is_recording: return False
        try:
            k = key.char
        except AttributeError:
            k = str(key)
        self.recording.append({"t": time.time() - self.start_time, "type": "key_down", "key": k})

    def on_release(self, key):
        if not self.is_recording: return False
        try:
            k = key.char
        except AttributeError:
            k = str(key)
            
        # Stop recording on ESC
        if key == keyboard.Key.esc:
            logger.info("ESC detected. Stopping macro recording.")
            self.stop_recording()
            return False

        self.recording.append({"t": time.time() - self.start_time, "type": "key_up", "key": k})

    def on_click(self, x, y, button, pressed):
        if not self.is_recording: return False
        self.recording.append({
            "t": time.time() - self.start_time,
            "type": "click",
            "x": x,
            "y": y,
            "button": str(button),
            "pressed": pressed
        })

    def start_recording(self, macro_name: str) -> str:
        if self.is_recording:
            return "Already recording!"
        
        self.current_macro_name = macro_name
        self.recording = []
        self.is_recording = True
        self.start_time = time.time()

        # Start listeners
        self.k_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.m_listener = mouse.Listener(on_click=self.on_click)
        
        self.k_listener.start()
        self.m_listener.start()
        
        logger.info(f"Started recording macro '{macro_name}'. Press ESC to stop.")
        return f"Recording macro '{macro_name}'. Perform your actions, then press ESC on your keyboard to save."

    def stop_recording(self) -> str:
        if not self.is_recording:
            return "Not currently recording a macro."
            
        self.is_recording = False
        if hasattr(self, 'k_listener'): self.k_listener.stop()
        if hasattr(self, 'm_listener'): self.m_listener.stop()
        
        if self.current_macro_name and len(self.recording) > 0:
            self.macros[self.current_macro_name] = self.recording
            with open(self.macro_file, "w") as f:
                json.dump(self.macros, f, indent=4)
            logger.info(f"Macro '{self.current_macro_name}' saved with {len(self.recording)} events.")
            return f"Macro '{self.current_macro_name}' saved successfully."
        return "Recording stopped. No events captured."

    def play_macro(self, macro_name: str) -> str:
        if macro_name not in self.macros:
            return f"Error: Macro '{macro_name}' not found."
            
        events = self.macros[macro_name]
        if not events:
            return f"Macro '{macro_name}' is empty."
            
        logger.info(f"Playing back macro '{macro_name}'...")
        k_ctrl = keyboard.Controller()
        m_ctrl = mouse.Controller()

        last_time = 0
        # Wait a sec before starting playback
        time.sleep(1.0)

        for event in events:
            t = event["t"]
            time.sleep(max(0, t - last_time))
            last_time = t

            if event["type"] == "click":
                m_ctrl.position = (event["x"], event["y"])
                btn = mouse.Button.left
                if 'right' in event["button"]: btn = mouse.Button.right
                if 'middle' in event["button"]: btn = mouse.Button.middle
                
                if event["pressed"]:
                    m_ctrl.press(btn)
                else:
                    m_ctrl.release(btn)
                    
            elif event["type"] == "key_down":
                key = self._parse_key(event["key"])
                if key: k_ctrl.press(key)
                
            elif event["type"] == "key_up":
                key = self._parse_key(event["key"])
                if key: k_ctrl.release(key)

        logger.info(f"Finished playing macro '{macro_name}'.")
        return f"Successfully executed macro '{macro_name}'."
        
    def _parse_key(self, k_str):
        if k_str.startswith("Key."):
            try:
                attr = k_str.split(".")[1]
                return getattr(keyboard.Key, attr)
            except AttributeError:
                return None
        return k_str
