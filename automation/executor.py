import os
import pyautogui
import subprocess
import time
from utils.helpers import setup_logger

logger = setup_logger("DesktopExecutor")

# Safety: raise exception if mouse moves to corner
pyautogui.FAILSAFE = True
# Small pause between every pyautogui call
pyautogui.PAUSE = 0.4


# Map common app names to Windows executable commands
APP_COMMANDS = {
    "chrome":        "start chrome",
    "google chrome": "start chrome",
    "brave":         "start brave",
    "brave browser": "start brave",
    "firefox":       "start firefox",
    "msedge":        "start msedge",
    "edge":          "start msedge",
    "opera":         "start opera",
    "notepad":       "start notepad",
    "calc":          "start calc",
    "calculator":    "start calc",
    "explorer":      "start explorer",
    "file explorer": "start explorer",
    "winword":       "start winword",
    "word":          "start winword",
    "excel":         "start excel",
    "powerpnt":      "start powerpnt",
    "powerpoint":    "start powerpnt",
    "mspaint":       "start mspaint",
    "paint":         "start mspaint",
    "cmd":           "start cmd",
    "powershell":    "start powershell",
    "taskmgr":       "start taskmgr",
    "code":          "start code",
    "vs code":       "start code",
    "vscode":        "start code",
    "snippingtool":  "start snippingtool",
    "control":       "start control",
    "wmplayer":      "start wmplayer",
    "vlc":           "start vlc",
    "spotify":       "start spotify",
    "telegram":      "start telegram",
    "discord":       "start discord",
    "zoom":          "start zoom",
    "teams":         "start ms-teams",
}


class DesktopExecutor:
    def __init__(self):
        pass

    def execute_action(self, action_dict: dict) -> bool:
        """
        Execute a single structured action dict.
        Returns True on success, False on failure.
        """
        if not isinstance(action_dict, dict):
            logger.warning(f"Invalid action received (not a dict): {action_dict}")
            return False

        action = action_dict.get("action", "").lower().strip()

        try:
            if action == "open_app":
                app = action_dict.get("app", "").lower().strip()
                return self._open_app(app)

            elif action == "open_file":
                path = action_dict.get("path", "").strip()
                if not path:
                    logger.warning("open_file action missing 'path'.")
                    return False
                try:
                    logger.info(f"Opening file/folder: {path}")
                    os.startfile(path)
                    time.sleep(1.0)
                    return True
                except Exception as e:
                    logger.error(f"Failed to open file '{path}': {e}")
                    return False

            elif action == "navigate_url":
                # Open or navigate to a URL in the currently active browser window
                # Uses Ctrl+L to focus the address bar then types the FULL URL at once
                url = action_dict.get("url", "").strip()
                if not url:
                    logger.warning("navigate_url action missing 'url'.")
                    return False
                try:
                    logger.info(f"Navigating browser to: {url}")
                    time.sleep(0.5)
                    pyautogui.hotkey("ctrl", "l")     # Focus address bar
                    time.sleep(0.4)
                    pyautogui.hotkey("ctrl", "a")     # Select all existing text
                    time.sleep(0.2)
                    # Use clipboard paste instead of write() to avoid word-split bugs
                    import pyperclip
                    pyperclip.copy(url)
                    pyautogui.hotkey("ctrl", "v")     # Paste full URL at once
                    time.sleep(0.3)
                    pyautogui.press("enter")
                    time.sleep(1.5)
                    return True
                except ImportError:
                    # Fallback without pyperclip
                    pyautogui.hotkey("ctrl", "l")
                    time.sleep(0.4)
                    pyautogui.hotkey("ctrl", "a")
                    pyautogui.write(url, interval=0.02)
                    pyautogui.press("enter")
                    return True
                except Exception as e:
                    logger.error(f"navigate_url failed: {e}")
                    return False

            elif action == "type":
                text = action_dict.get("text", "")
                logger.info(f"Typing: {text}")
                pyautogui.write(str(text), interval=0.04)
                return True

            elif action == "press":
                key = action_dict.get("key", "").lower().strip()
                if not key:
                    return False
                logger.info(f"Pressing key: {key}")
                try:
                    pyautogui.press(key)
                    return True
                except Exception as e:
                    logger.error(f"Failed to press key '{key}': {e}")
                    return False

            elif action == "hotkey":
                keys = action_dict.get("keys", [])
                if not keys:
                    logger.warning("Hotkey action received with no keys.")
                    return False
                logger.info(f"Pressing hotkey: {keys}")
                try:
                    pyautogui.hotkey(*[k.lower() for k in keys])
                    return True
                except Exception as e:
                    logger.error(f"Failed to press hotkey {keys}: {e}")
                    return False

            elif action == "click":
                x = action_dict.get("x")
                y = action_dict.get("y")
                if x is not None and y is not None:
                    logger.info(f"Clicking at ({x}, {y})")
                    pyautogui.click(int(x), int(y))
                    return True
                logger.warning("Click action missing x or y coordinates.")
                return False

            elif action == "wait":
                seconds = float(action_dict.get("seconds", 1))
                logger.info(f"Waiting {seconds} seconds...")
                time.sleep(seconds)
                return True

            elif action == "move":
                x = action_dict.get("x")
                y = action_dict.get("y")
                if x is not None and y is not None:
                    pyautogui.moveTo(int(x), int(y), duration=0.3)
                    return True
                return False

            elif action == "setup_workspace":
                workspace_type = action_dict.get("type", "coding")
                from automation.workspace import WorkspaceManager
                wm = WorkspaceManager()
                if workspace_type == "coding":
                    wm.setup_coding_environment()
                elif workspace_type == "research":
                    wm.setup_research_environment()
                return True

            elif action == "toggle_lights":
                state = action_dict.get("state", True)
                from automation.smart_home import SmartHomeManager
                shm = SmartHomeManager()
                shm.toggle_lights(state)
                return True

            elif action == "read_emails":
                from automation.email_calendar import EmailCalendarAgent
                agent = EmailCalendarAgent()
                result = agent.check_unread_emails()
                logger.info(f"Emails: {result}")
                return True

            elif action == "local_search":
                query = action_dict.get("query", "")
                from database.local_indexer import LocalFileIndexer
                indexer = LocalFileIndexer()
                result = indexer.search(query)
                logger.info(f"Local Search Result: {result}")
                return True

            else:
                logger.warning(f"Unknown action type: '{action}' in {action_dict}")
                return False

        except Exception as e:
            logger.error(f"Failed to execute action {action_dict}: {e}")
            return False

    def _is_process_running(self, app_name: str) -> bool:
        """Check if any process is running with a name containing app_name."""
        import psutil
        app_name_lower = app_name.lower().strip()
        
        # Common mappings from app query to actual process executable names
        proc_mappings = {
            "paint": "mspaint",
            "word": "winword",
            "excel": "excel",
            "powerpoint": "powerpnt",
            "vs code": "code",
            "vscode": "code",
            "msedge": "msedge",
            "edge": "msedge",
            "calculator": "calc",
            "chrome": "chrome",
            "google chrome": "chrome",
            "notepad": "notepad",
            "explorer": "explorer",
            "file explorer": "explorer",
            "cmd": "cmd",
            "powershell": "powershell",
            "vlc": "vlc",
            "spotify": "spotify",
            "discord": "discord",
        }
        target_name = proc_mappings.get(app_name_lower, app_name_lower)
        
        for proc in psutil.process_iter(['name']):
            try:
                pname = proc.info['name']
                if pname and target_name in pname.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def _open_app(self, app_name: str) -> bool:
        """Open an application by name using Windows shell commands and verify execution."""
        logger.info(f"Opening app: {app_name}")

        # Check if we have a direct shell command for it
        shell_cmd = APP_COMMANDS.get(app_name)
        if shell_cmd:
            try:
                subprocess.Popen(shell_cmd, shell=True)
                # Poll process list to verify successful start
                for _ in range(8):
                    time.sleep(0.5)
                    if self._is_process_running(app_name):
                        logger.info(f"Verified process started via shell: {app_name}")
                        return True
                logger.warning(f"Process not verified in process list yet, but shell command completed: {shell_cmd}")
                return True  # Fallback to True since command succeeded
            except Exception as e:
                logger.error(f"subprocess failed for '{app_name}': {e}")

        # Fallback: use Windows Start menu search (pyautogui)
        try:
            logger.info(f"App '{app_name}' not in APP_COMMANDS. Attempting Windows Search fallback...")
            pyautogui.hotkey('win', 's')   # Open Windows Search
            time.sleep(0.8)
            pyautogui.write(app_name, interval=0.05)
            time.sleep(1.0)
            pyautogui.press('enter')
            
            # Poll process list to verify start
            for _ in range(8):
                time.sleep(0.5)
                if self._is_process_running(app_name):
                    logger.info(f"Verified process started via Search fallback: {app_name}")
                    return True
                    
            logger.warning(f"Process verification failed for fallback: {app_name}")
            return False  # Failed to open
        except Exception as e:
            logger.error(f"Failed to open app via Start menu: {e}")
            return False
