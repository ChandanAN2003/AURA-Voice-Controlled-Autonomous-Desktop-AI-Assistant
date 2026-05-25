import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.config import FRONTEND_DIR, APP_NAME

app = FastAPI(title=APP_NAME, version="1.0.0")

# ── CORS (allow browser to call the API) ─────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routes ────────────────────────────────────────────────────────────────
# We import the router here to avoid circular imports at module level
from backend.api_routes import api_router   # noqa: E402
app.include_router(api_router, prefix="/api")

# ── Static Frontend ───────────────────────────────────────────────────────────
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    print(f"[!] Frontend directory not found at {FRONTEND_DIR}")


@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print(f"  {APP_NAME}")
    print("  Backend API  ->  http://127.0.0.1:8000")
    print("  Frontend UI  ->  http://127.0.0.1:8000")
    print("=" * 60)

    # Start proactive background agent
    try:
        from automation.proactive import ProactiveAgent
        from voice.text_to_speech import get_tts_engine
        tts = get_tts_engine()
        agent = ProactiveAgent(tts_engine=tts)
        agent.start()
        # Keep a reference so it isn't garbage collected
        app.state.proactive_agent = agent
    except Exception as e:
        print(f"[!] Failed to start Proactive Agent: {e}")
