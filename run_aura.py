import uvicorn
import os
import sys

def main():
    """
    Entry point for the AURA AI Assistant.
    Starts the FastAPI backend.
    """
    print("="*60)
    print("Starting AURA – Autonomous Voice Controlled Desktop AI Assistant")
    print("="*60)

    # Ensure python path is correct for local module imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    print("[*] Launching API Server on http://127.0.0.1:8000")
    print("[*] Please ensure Ollama is running (`ollama serve`)")
    
    # Run the FastAPI app via uvicorn
    # Make sure backend.main exists before running
    try:
        uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True, log_level="info")
    except Exception as e:
        print(f"[!] Error starting server: {e}")

if __name__ == "__main__":
    main()
