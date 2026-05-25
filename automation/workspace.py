import time
import subprocess
import os

try:
    import pygetwindow as gw
except ImportError:
    gw = None

from utils.helpers import setup_logger

logger = setup_logger("WorkspaceManager")

class WorkspaceManager:
    def __init__(self):
        pass

    def setup_coding_environment(self) -> str:
        """
        Sets up a standard coding workspace.
        Opens VS Code, browser, and terminal.
        """
        logger.info("Setting up coding workspace...")
        
        try:
            # Open VS Code
            subprocess.Popen("start code", shell=True)
            time.sleep(2)
            
            # Open Browser (Chrome)
            subprocess.Popen("start chrome https://github.com https://chatgpt.com", shell=True)
            time.sleep(2)
            
            # Open Terminal
            subprocess.Popen("start cmd", shell=True)
            
            if gw:
                # Optionally snap windows if pygetwindow is available
                # (Complex on Windows, mock for now)
                pass
                
            return "Coding workspace is set up and ready."
        except Exception as e:
            logger.error(f"Failed to setup coding environment: {e}")
            return f"Failed to set up workspace: {e}"

    def setup_research_environment(self) -> str:
        """
        Sets up a standard research workspace.
        """
        logger.info("Setting up research workspace...")
        try:
            subprocess.Popen("start chrome https://scholar.google.com https://en.wikipedia.org", shell=True)
            subprocess.Popen("start notepad", shell=True)
            return "Research workspace initialized."
        except Exception as e:
            logger.error(f"Failed to setup research environment: {e}")
            return "Failed to set up research environment."
