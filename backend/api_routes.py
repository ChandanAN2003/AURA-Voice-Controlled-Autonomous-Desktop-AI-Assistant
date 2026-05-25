import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ai_engine.planner import Planner
from automation.executor import DesktopExecutor
from database.db_manager import DBManager
from database.vector_memory import VectorMemory
from voice.text_to_speech import TextToSpeech
from voice.speech_to_text import SpeechToText
from vision.screen_capture import ScreenCapture
from vision.ocr_reader import OCRReader
from utils.helpers import setup_logger

# Advanced Features
from vision.screen_analyzer import ScreenAnalyzer
from security.face_auth import FaceAuthenticator
from automation.researcher import WebResearcher
from automation.macro_recorder import MacroRecorder
from ai_engine.reflection import ReflectionModule

logger = setup_logger("API_Routes")

# ── Thread pool for running blocking (sync) calls inside async endpoints ──────
_executor = ThreadPoolExecutor(max_workers=4)

# ── Module Singletons ─────────────────────────────────────────────────────────
planner  = Planner()
executor = DesktopExecutor()
db       = DBManager()
memory   = VectorMemory()
tts      = TextToSpeech()
stt      = SpeechToText()
screen   = ScreenCapture()
ocr      = OCRReader()

# Adv Singletons
vision_ai = ScreenAnalyzer()
face_sec  = FaceAuthenticator()
research  = WebResearcher()
macro_rec = MacroRecorder()
reflection = ReflectionModule()

# ── Router ────────────────────────────────────────────────────────────────────
api_router = APIRouter()


class CommandRequest(BaseModel):
    command: str


async def _run_in_thread(func, *args):
    """Run a blocking (sync) function in a thread pool so the event loop stays free."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, func, *args)


@api_router.post("/execute")
async def execute_command(req: CommandRequest):
    """Receive a command, plan it with the AI, execute it on the desktop."""
    logger.info(f"Received command: {req.command}")

    if not req.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty.")

    cmd = req.command.lower()

    # --- ADVANCED FEATURE ROUTING ---
    # 1. Face ID
    if any(k in cmd for k in ["authenticate", "face id", "verify me"]):
        success = await _run_in_thread(face_sec.verify_user)
        msg = "Face SECURELY Verified. Access granted." if success else "Face verification FAILED. Access denied."
        return {"status": "SUCCESS" if success else "FAILED", "message": msg, "plan": [], "logs": [msg]}

    # 2. Web Researcher
    if cmd.startswith("research "):
        topic = req.command[9:].strip()
        msg = await _run_in_thread(research.research_topic, topic)
        return {"status": "SUCCESS" if "saved" in msg else "FAILED", "message": msg, "plan": [], "logs": [f"Research: {msg}"]}

    # 3. Vision AI
    if any(k in cmd for k in ["what's on my screen", "what is on my screen", "look at my screen", "describe my screen"]):
        msg = await _run_in_thread(vision_ai.analyze, req.command)
        return {"status": "SUCCESS" if not msg.startswith("Error") else "FAILED", "message": f"<b>Vision Analysis:</b><br>{msg}", "plan": [], "logs": ["Vision check complete."]}

    # 4. Macro Recording
    if cmd.startswith("start recording"):
        m_name = req.command.replace("start recording", "").strip() or "default"
        msg = macro_rec.start_recording(m_name)
        return {"status": "SUCCESS", "message": msg, "plan": [], "logs": [msg]}
    if cmd.startswith("stop recording") or cmd == "stop":
        msg = macro_rec.stop_recording()
        return {"status": "SUCCESS", "message": msg, "plan": [], "logs": [msg]}
    if cmd.startswith("run macro") or cmd.startswith("play macro"):
        m_name = req.command.replace("run macro", "").replace("play macro", "").strip() or "default"
        msg = await _run_in_thread(macro_rec.play_macro, m_name)
        return {"status": "SUCCESS" if "Successfully" in msg else "FAILED", "message": msg, "plan": [], "logs": [msg]}
    # --------------------------------

    # 1. Memory context (non-blocking, best-effort)
    try:
        context = await _run_in_thread(memory.search_memory, req.command)
        logger.info(f"Memory context retrieved: {len(context)} entries")
    except Exception as e:
        logger.warning(f"Memory search failed (non-fatal): {e}")
        context = []

    # 2. Generate plan — this blocks on Ollama, must run in thread
    plan = await _run_in_thread(planner.generate_plan, req.command)

    if not plan:
        logger.error("Planner returned an empty plan.")
        try:
            db.save_task(
                command=req.command,
                ai_response="Failed to generate execution plan.",
                steps="[]",
                status="FAILED",
            )
        except Exception:
            pass
        return JSONResponse(
            status_code=200,
            content={
                "status": "FAILED",
                "message": (
                    "AURA could not generate a plan for that command. "
                    "If Ollama is offline, start it with: ollama serve  "
                    f"and pull the model: ollama pull {planner.client.model}"
                ),
                "plan": [],
                "logs": [],
            },
        )

    # 3. Execute steps — pyautogui is also blocking
    execution_logs = []
    status = "SUCCESS"

    # Speak async (already runs in daemon thread inside TextToSpeech)
    tts.speak(f"Executing: {req.command}")

    for step in plan:
        success = await _run_in_thread(executor.execute_action, step)
        log_line = f"Step: {step}  —  {'✓ OK' if success else '✗ FAILED'}"
        execution_logs.append(log_line)
        logger.info(log_line)
        if not success:
            status = "FAILED"
            break
        await asyncio.sleep(0.3)   # non-blocking pause between steps

    # 4. Screenshot + OCR (best-effort, won't crash the response)
    visible_text = ""
    try:
        screenshot_path = await _run_in_thread(screen.capture)
        visible_text     = await _run_in_thread(ocr.extract_text, screenshot_path)
    except Exception as e:
        logger.warning(f"Vision step failed (non-fatal): {e}")

    # --- ADVANCED REFLECTION MODULE CHECK ---
    # Only run reflection if executor thinks execution succeeded, to check for silent/visual failures
    reflection_reason = ""
    if status == "SUCCESS":
        try:
            logger.info("Running Reflection Module to verify execution success...")
            logs_str = "\n".join(execution_logs)
            reflection_res = await _run_in_thread(reflection.evaluate_success, req.command, logs_str, visible_text)
            logger.info(f"Reflection Module returned: {reflection_res}")
            
            if "STATUS: FAILED" in reflection_res:
                status = "FAILED"
                reflection_reason = reflection_res.replace("STATUS: FAILED", "").strip()
                logger.warning(f"Reflection flagged execution as FAILED. Reason: {reflection_reason}")
        except Exception as e:
            logger.warning(f"Reflection Module failed (non-fatal): {e}")

    # 5. Build response
    if status == "SUCCESS":
        response_msg = "Task completed successfully."
        tts.speak("Task completed.")
    else:
        if reflection_reason:
            # Clean up formatting for the user
            clean_reason = reflection_reason.replace("\n", " ").replace("STATUS: FAILED", "").strip()
            response_msg = f"Task verification failed: {clean_reason}"
        else:
            response_msg = "I encountered an error while executing the task."
        tts.speak("There was an error executing the task.")

    # 6. Persist to DB / memory (best-effort)
    try:
        db.save_task(
            command=req.command,
            ai_response=response_msg,
            steps=str(plan),
            status=status,
        )
        memory.add_memory(
            f"Command: {req.command} | Plan: {plan} | Status: {status}"
        )
    except Exception as e:
        logger.warning(f"Storage step failed (non-fatal): {e}")

    return {
        "status": status,
        "message": response_msg,
        "plan": plan,
        "logs": execution_logs,
        "visible_text_snippet": visible_text[:300] if visible_text else "",
    }


@api_router.get("/history")
async def get_history():
    """Return recent task history from SQLite."""
    try:
        tasks = await _run_in_thread(db.get_recent_tasks, 10)
        return {"history": tasks}
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        return {"history": []}


@api_router.get("/listen")
async def trigger_listen():
    """Trigger microphone listening and return transcribed text."""
    try:
        tts.speak("I am listening.")
        text = await _run_in_thread(stt.listen, 7)
        return {"heard": text}
    except Exception as e:
        logger.error(f"Listen endpoint error: {e}")
        return {"heard": "", "error": str(e)}


@api_router.get("/status")
async def get_status():
    """Health check – also reports whether Ollama is reachable."""
    ollama_ok = await _run_in_thread(planner.client.is_available)
    return {
        "api": "online",
        "ollama": "connected" if ollama_ok else "offline — run 'ollama serve'",
        "model": planner.client.model,
    }

import psutil

@api_router.get("/system_stats")
async def get_system_stats():
    """Return real-time CPU and Memory stats for the advanced HUD."""
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    return {
        "cpu_percent": cpu,
        "ram_percent": mem.percent,
        "ram_used_gb": round(mem.used / (1024 ** 3), 1),
        "ram_total_gb": round(mem.total / (1024 ** 3), 1)
    }

