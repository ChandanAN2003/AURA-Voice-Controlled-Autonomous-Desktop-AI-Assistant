import os
import re
import glob
import subprocess
from ai_engine.ollama_client import OllamaClient
from ai_engine.gemini_client import GeminiClient
from utils.helpers import setup_logger, parse_json_safely

logger = setup_logger("AIPlanner")

# ── Known applications ────────────────────────────────────────────────────────
APP_MAP = {
    "chrome":              "chrome",
    "google chrome":       "chrome",
    "brave":               "brave",
    "brave browser":       "brave",
    "firefox":             "firefox",
    "mozilla firefox":     "firefox",
    "edge":                "msedge",
    "microsoft edge":      "msedge",
    "opera":               "opera",
    "notepad":             "notepad",
    "notepad++":           "notepad++",
    "calculator":          "calc",
    "file explorer":       "explorer",
    "explorer":            "explorer",
    "this pc":             "explorer",
    "my computer":         "explorer",
    "word":                "winword",
    "microsoft word":      "winword",
    "excel":               "excel",
    "microsoft excel":     "excel",
    "powerpoint":          "powerpnt",
    "paint":               "mspaint",
    "cmd":                 "cmd",
    "command prompt":      "cmd",
    "terminal":            "cmd",
    "powershell":          "powershell",
    "task manager":        "taskmgr",
    "vs code":             "code",
    "vscode":              "code",
    "visual studio code":  "code",
    "vlc":                 "vlc",
    "spotify":             "spotify",
    "teams":               "teams",
    "microsoft teams":     "teams",
    "zoom":                "zoom",
    "whatsapp":            "whatsapp",
    "telegram":            "telegram",
    "discord":             "discord",
    "slack":               "slack",
    "snipping tool":       "snippingtool",
    "settings":            "ms-settings:",
    "control panel":       "control",
    "winamp":              "winamp",
    "windows media player": "wmplayer",
}

# Common locations to search for files/folders
SEARCH_LOCATIONS = [
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/OneDrive/Desktop"),
    os.path.expanduser("~/OneDrive/Documents"),
    "C:/Users/Public/Desktop",
]


class Planner:
    def __init__(self):
        self.ollama = OllamaClient()
        self.gemini = GeminiClient()

    def _is_complex_command(self, command: str) -> bool:
        """
        Detect if a command is complex or compound (e.g., contains multiple instructions).
        Compound commands should ALWAYS bypass rule-based matching to let the LLM generate 
        a complete, cohesive plan instead of returning a partial/truncated rule-based plan.
        """
        cmd = command.lower().strip()
        
        # Conjunctions or transitions indicating multiple sequential steps
        conjunctions = [
            " and ", " then ", " then open ", " then type ", " then press ", " after that ",
            " after ", " before ", " next ", " and write ", " and search ", " and play ",
            " and click ", " and click on "
        ]
        
        # Check for multiple known action triggers in the same command
        action_verbs = ["open", "type", "press", "write", "search", "play", "mute", "screenshot", "minimize", "maximize", "close"]
        verb_count = sum(1 for verb in action_verbs if f" {verb} " in f" {cmd} ")
        
        if any(conj in cmd for conj in conjunctions) or verb_count >= 2:
            logger.info(f"Command '{command}' classified as COMPLEX (verb count: {verb_count}). Bypassing rule-based planner.")
            return True
            
        return False

    def generate_plan(self, command: str) -> list:
        """
        Converts a natural language command into a list of structured action steps.
        Tries rule-based planner first ONLY for simple, single-action commands.
        Bypasses rule-based planner and uses Gemini/Ollama AI for complex, multi-action commands.
        """
        logger.info(f"Generating plan for: {command}")

        # 1. Try rule-based planner ONLY if command is NOT complex/compound
        if not self._is_complex_command(command):
            plan = self._rule_based_plan(command)
            if plan:
                logger.info(f"Rule-based plan succeeded with {len(plan)} steps.")
                return plan

        # 2. If no rule matched or it was complex, check for AI planners
        response = None
        system_prompt = self._ai_prompt()

        # Try Gemini API first (much faster, more powerful, requires no local server resources)
        if self.gemini.is_available():
            logger.info("Using cloud-based Gemini API for planning...")
            response = self.gemini.generate(command, system_prompt=system_prompt)
            if response and not response.startswith("Error"):
                ai_plan = parse_json_safely(response)
                if ai_plan:
                    logger.info(f"Gemini plan generated successfully with {len(ai_plan)} steps.")
                    return ai_plan
                logger.warning(f"Could not parse Gemini response as JSON: {response[:200]}")
            else:
                logger.warning(f"Gemini API returned error or empty response: {response}")

        # Fallback to local Ollama AI
        if self.ollama.is_available():
            logger.info("Using local Ollama AI for planning...")
            response = self.ollama.generate(command, system_prompt=system_prompt)
            if response and not response.startswith("Error"):
                ai_plan = parse_json_safely(response)
                if ai_plan:
                    logger.info(f"Ollama plan generated successfully with {len(ai_plan)} steps.")
                    return ai_plan
                logger.warning(f"Could not parse Ollama response as JSON: {response[:200]}")
            else:
                logger.warning(f"Ollama AI returned error or empty response: {response}")

        # If both failed and rule-based wasn't run (because it was complex), try rule-based as a last-ditch effort
        if self._is_complex_command(command):
            logger.warning("AI planners failed. Attempting rule-based planner as fallback for complex command...")
            plan = self._rule_based_plan(command)
            if plan:
                return plan

        logger.error("Both Gemini API and Ollama AI failed to generate an execution plan.")
        return []

    # ── AI prompt ─────────────────────────────────────────────────────────────
    def _ai_prompt(self) -> str:
        return (
            "You are a desktop automation AI. Convert the user command into a JSON array of steps.\n"
            "Only use these action types:\n"
            '  {"action": "open_app",  "app": "<app name>"}\n'
            '  {"action": "open_file", "path": "<absolute file path>"}\n'
            '  {"action": "type",      "text": "<text to type>"}\n'
            '  {"action": "press",     "key": "<key name>"}\n'
            '  {"action": "hotkey",    "keys": ["<key1>", "<key2>"]}\n'
            '  {"action": "wait",      "seconds": <number>}\n\n'
            "Rules:\n"
            "- Return ONLY a valid JSON array, nothing else.\n"
            "- No markdown, no explanation, no code fences.\n\n"
            "Example for 'open chrome and search for AI news':\n"
            '[{"action":"open_app","app":"chrome"},{"action":"wait","seconds":2},'
            '{"action":"type","text":"AI news"},{"action":"press","key":"enter"}]'
        )

    # ── Core Rule-Based Planner ───────────────────────────────────────────────
    def _rule_based_plan(self, command: str) -> list:
        """
        Comprehensive keyword/pattern planner — handles music, browser, apps,
        files, volume, typing, and system commands.
        """
        cmd = command.lower().strip()
        plan = []

        # ── 1. Music / Song / Play detection (MUST be before app detection) ────
        # Handles: "play khat song", "open brave and play khat song",
        #          "play khat on youtube", "search khat on youtube"
        music_plan = self._try_play_music(cmd, command)
        if music_plan:
            return music_plan

        # ── 2. Open local file / folder on Desktop or common locations ────────
        file_plan = self._try_open_local(cmd, command)
        if file_plan:
            return file_plan

        # ── 3. Screenshot ──────────────────────────────────────────────────────
        if any(k in cmd for k in ["screenshot", "take a screenshot", "capture screen", "print screen"]):
            plan.append({"action": "press", "key": "printscreen"})
            return plan

        # ── 4. Volume controls ─────────────────────────────────────────────────
        if any(k in cmd for k in ["volume up", "increase volume", "louder"]):
            times = self._extract_number(cmd) or 3
            for _ in range(int(times)):
                plan.append({"action": "press", "key": "volumeup"})
            return plan

        if any(k in cmd for k in ["volume down", "decrease volume", "quieter", "lower volume"]):
            times = self._extract_number(cmd) or 3
            for _ in range(int(times)):
                plan.append({"action": "press", "key": "volumedown"})
            return plan

        if any(k in cmd for k in ["mute", "unmute", "silence"]):
            plan.append({"action": "press", "key": "volumemute"})
            return plan

        # ── 5. Known app opening ───────────────────────────────────────────────
        opened_app = None
        for keyword in sorted(APP_MAP.keys(), key=len, reverse=True):  # longest match first
            if keyword in cmd:
                app_cmd = APP_MAP[keyword]
                plan.append({"action": "open_app", "app": app_cmd})
                plan.append({"action": "wait", "seconds": 2})
                opened_app = app_cmd
                break

        # ── 6. Browser search (uses navigate URL, NOT raw typing) ─────────────
        search_query = self._extract_search_query(cmd)
        if search_query:
            browser = opened_app if opened_app in ("chrome", "brave", "msedge", "firefox") else None
            if not browser:
                plan.append({"action": "open_app", "app": "chrome"})
                plan.append({"action": "wait", "seconds": 2})
            # Navigate directly using URL — avoids the word-split tab bug
            search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            plan.append({"action": "navigate_url", "url": search_url})
            return plan

        # ── 7. YouTube (direct URL navigation) ────────────────────────────────
        if "youtube" in cmd:
            query = re.sub(r"\b(open|play|search|on|in|youtube|go\s+to)\b", "", cmd).strip()
            query = query.strip(" ,") or "music"
            browser = opened_app if opened_app in ("chrome", "brave", "msedge", "firefox") else None
            if not browser:
                plan.append({"action": "open_app", "app": "chrome"})
                plan.append({"action": "wait", "seconds": 2})
            yt_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            plan.append({"action": "navigate_url", "url": yt_url})
            return plan

        # ── 8. Type / write text ───────────────────────────────────────────────
        for kw in ["type ", "write ", "input "]:
            if kw in cmd:
                text = command[command.lower().index(kw) + len(kw):].strip()
                plan.append({"action": "type", "text": text})
                return plan

        # ── 9. Close / quit ────────────────────────────────────────────────────
        if any(k in cmd for k in ["close window", "close app", "quit", "exit app"]):
            plan.append({"action": "hotkey", "keys": ["alt", "f4"]})
            return plan

        # ── 9. Minimize / maximize ─────────────────────────────────────────────
        if any(k in cmd for k in ["minimize", "minimise"]):
            plan.append({"action": "hotkey", "keys": ["win", "down"]})
            return plan

        if any(k in cmd for k in ["maximize", "maximise"]):
            plan.append({"action": "hotkey", "keys": ["win", "up"]})
            return plan

        # ── 10. Lock screen ────────────────────────────────────────────────────
        if any(k in cmd for k in ["lock", "lock screen", "lock pc", "lock computer"]):
            plan.append({"action": "hotkey", "keys": ["win", "l"]})
            return plan

        # ── 11. Show desktop ───────────────────────────────────────────────────
        if any(k in cmd for k in ["show desktop", "go to desktop", "minimize all"]):
            plan.append({"action": "hotkey", "keys": ["win", "d"]})
            return plan

        # ── 12. Advanced Workspace Management ──────────────────────────────────
        if any(k in cmd for k in ["coding workspace", "set up my coding", "coding environment"]):
            plan.append({"action": "setup_workspace", "type": "coding"})
            return plan
        
        if any(k in cmd for k in ["research workspace", "research environment"]):
            plan.append({"action": "setup_workspace", "type": "research"})
            return plan

        # ── 13. Smart Home Control ─────────────────────────────────────────────
        if any(k in cmd for k in ["lights on", "turn on the lights", "turn on lights"]):
            plan.append({"action": "toggle_lights", "state": True})
            return plan

        if any(k in cmd for k in ["lights off", "turn off the lights", "turn off lights", "dim the lights"]):
            plan.append({"action": "toggle_lights", "state": False})
            return plan

        # ── 14. Email & Calendar ───────────────────────────────────────────────
        if any(k in cmd for k in ["check emails", "read emails", "read my emails"]):
            plan.append({"action": "read_emails"})
            return plan

        # ── 15. Local Semantic Search ──────────────────────────────────────────
        if "local search" in cmd or "search my documents for" in cmd:
            query = cmd.replace("local search", "").replace("search my documents for", "").strip()
            plan.append({"action": "local_search", "query": query})
            return plan

        # ── 15b. Simple Key Press / Hotkey (e.g. "press enter", "press space", "press windows key") ──
        key_words = cmd.split()
        if len(key_words) >= 2 and key_words[0] in ("press", "hit", "tap"):
            target_key = cmd.replace(key_words[0], "").strip()
            # Clean up key name
            target_key = target_key.replace("key", "").strip()
            valid_keys = {
                "enter": "enter", "return": "enter",
                "space": "space", "spacebar": "space",
                "backspace": "backspace",
                "tab": "tab",
                "escape": "esc", "esc": "esc",
                "win": "win", "windows": "win",
                "up": "up", "down": "down", "left": "left", "right": "right",
                "volumeup": "volumeup", "volumedown": "volumedown", "volumemute": "volumemute"
            }
            if target_key in valid_keys:
                plan.append({"action": "press", "key": valid_keys[target_key]})
                return plan

        # ── 16. If app was opened but no other action — still return it ────────
        if plan:
            return plan

        logger.warning(f"Rule-based planner could not handle: {command}")
        return []

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _try_open_local(self, cmd: str, original_command: str) -> list:
        """
        Detect 'open <name>' or 'in desktop open <name>' patterns and
        find the matching file/folder on common locations. Returns plan or [].
        """
        # Patterns: "open X", "open X on desktop", "in desktop open X",
        #           "on desktop open X", "launch X", "run X"
        open_patterns = [
            r"(?:in |on )?desktop\s+open\s+(.+)",
            r"open\s+(.+?)(?:\s+on\s+desktop|\s+on\s+desktop|\s+in\s+desktop)?$",
            r"(?:launch|run|start)\s+(.+)",
        ]

        target_name = None
        for pattern in open_patterns:
            match = re.search(pattern, cmd)
            if match:
                raw = match.group(1).strip()
                # Remove trailing filler words
                raw = re.sub(r"\s+(on|in|the|from)\s+(desktop|my desktop|documents|downloads)$", "", raw).strip()
                # Skip if it's a known app keyword (handled by app_map)
                if not any(raw in k or k in raw for k in APP_MAP):
                    target_name = raw
                    break

        if not target_name:
            return []

        logger.info(f"Searching for local item: '{target_name}'")

        # Search Desktop and common folders
        found_path = self._find_local_item(target_name)

        if found_path:
            logger.info(f"Found local item at: {found_path}")
            return [{"action": "open_file", "path": found_path}]

        # If not found, try opening via Run dialog (Win+R)
        logger.warning(f"Local item '{target_name}' not found in common locations — trying Win+R")
        return [
            {"action": "hotkey", "keys": ["win", "r"]},
            {"action": "wait", "seconds": 0.5},
            {"action": "type", "text": target_name},
            {"action": "press", "key": "enter"},
        ]

    def _find_local_item(self, name: str) -> str | None:
        """
        Search Desktop and common locations for a file/folder matching `name`.
        Uses fuzzy prefix matching (case-insensitive).
        """
        name_lower = name.lower().replace(" ", "")

        for location in SEARCH_LOCATIONS:
            if not os.path.exists(location):
                continue
            try:
                for entry in os.scandir(location):
                    entry_lower = entry.name.lower().replace(" ", "")
                    # Exact match
                    if entry_lower == name_lower:
                        return entry.path
                    # Name without extension matches
                    base = os.path.splitext(entry.name)[0].lower().replace(" ", "")
                    if base == name_lower:
                        return entry.path
                    # Starts-with match
                    if entry_lower.startswith(name_lower) or name_lower.startswith(entry_lower):
                        return entry.path
            except PermissionError:
                continue

        return None

    def _extract_search_query(self, cmd: str) -> str | None:
        """Extract what the user wants to search for."""
        triggers = [
            "search for ", "search ", "look up ", "google ",
            "find ", "browse ", "go to ",
        ]
        for trigger in triggers:
            if trigger in cmd:
                # Don't match things like "search for a file on desktop"
                query = cmd.split(trigger, 1)[1].strip()
                # If it has desktop/local words it's a local command not a web search
                if not any(w in query for w in ["desktop", "folder", "file", "my pc", "local"]):
                    return query
        return None

    def _extract_number(self, text: str) -> int | None:
        """Extract first integer from text."""
        match = re.search(r"\d+", text)
        return int(match.group()) if match else None

    def _try_play_music(self, cmd: str, original_command: str) -> list:
        """
        Detect music/song/play commands and search on YouTube.
        Handles patterns like:
          - "play khat song"
          - "open brave and play khat song"
          - "play khat by AP Dhillon"
          - "play some lofi music"
          - "search khat on youtube"
        """
        # Keywords that trigger music mode
        music_keywords = ["play ", "play a ", "song", "music", "track", "album", "artist"]
        is_music_cmd = any(k in cmd for k in music_keywords)

        if not is_music_cmd:
            return []

        # Detect which browser to use (if specified in command)
        browser_app = "chrome"  # default
        for keyword in ["brave", "firefox", "edge", "chrome"]:
            if keyword in cmd:
                browser_app = APP_MAP.get(keyword, "chrome")
                break

        # Extract song/music name by stripping control words
        filler_words = [
            r"\bopen\b", r"\bplay\b", r"\bplaying\b", r"\bsong\b", r"\bsongs\b",
            r"\bmusic\b", r"\btrack\b", r"\bvideo\b", r"\bthe\b", r"\ba\b",
            r"\bon\b", r"\bin\b", r"\busing\b", r"\bwith\b", r"\band\b",
            r"\byoutube\b", r"\bspotify\b", r"\bbrave\b", r"\bchrome\b",
            r"\bfirefox\b", r"\bedge\b", r"\bbrowser\b", r"\bfor\b", r"\bme\b",
            r"\bsome\b", r"\bplease\b",
        ]
        song_name = cmd
        for filler in filler_words:
            song_name = re.sub(filler, "", song_name, flags=re.IGNORECASE)

        song_name = re.sub(r"\s+", " ", song_name).strip(" ,.-")

        if not song_name:
            song_name = "latest songs"  # fallback

        logger.info(f"Music command detected. Song: '{song_name}', Browser: '{browser_app}'")

        yt_url = f"https://www.youtube.com/results?search_query={song_name.replace(' ', '+')}"

        return [
            {"action": "open_app", "app": browser_app},
            {"action": "wait", "seconds": 2},
            {"action": "navigate_url", "url": yt_url},
        ]
