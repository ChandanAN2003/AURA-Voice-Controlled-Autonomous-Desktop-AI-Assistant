import os

# Load .env file manually if it exists in the root directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

# Application Settings
APP_NAME = "AURA - Autonomous Voice AI Assistant"
DEBUG = True
HOST = "127.0.0.1"
PORT = 8000

# Ollama Model Settings
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3"

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "aura_memory.db")
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "database", "faiss_index.bin")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# External API (Optional)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
