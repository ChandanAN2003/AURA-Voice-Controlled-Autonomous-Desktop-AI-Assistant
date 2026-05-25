import os

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
