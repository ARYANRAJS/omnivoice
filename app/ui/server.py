import os
import shutil
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.stt import whisper
from app.llm import ollama
from app.tts import factory as tts_factory
from app.agent import router, memory, graph_memory, async_worker
from app.audio import playback
from app.tools import vision_tool

logger = logging.getLogger(__name__)

app = FastAPI(title="OmniVoice Voice AI Agent Server")

UI_DIR = os.path.join(os.path.dirname(__file__))
app.mount("/static", StaticFiles(directory=UI_DIR), name="static")

class TextChatRequest(BaseModel):
    text: str

class ConfigUpdateRequest(BaseModel):
    ollama_model: Optional[str] = None
    tts_provider: Optional[str] = None
    voice_reference_audio: Optional[str] = None
    voice_reference_text: Optional[str] = None

class VisionAnalyzeRequest(BaseModel):
    image_base64: str
    prompt: Optional[str] = "Describe what you see in this image in detail."

@app.get("/")
async def get_index():
    return FileResponse(os.path.join(UI_DIR, "index.html"))

@app.get("/api/status")
async def get_status():
    ollama_online, ollama_msg = await ollama.check_ollama_status()
    voices_dir = getattr(settings, 'VOICES_DIR', os.path.join(settings.BASE_DIR, "voices"))
    voices = [f for f in os.listdir(voices_dir) if f.endswith('.wav')]
    
    return {
        "status": playback.get_current_status(),
        "is_running": playback.is_playing(),
        "error_message": "",
        "ollama_online": ollama_online,
        "ollama_message": ollama_msg,
        "active_model": settings.OLLAMA_MODEL,
        "active_provider": settings.TTS_PROVIDER,
        "active_voice": settings.VOICE_REFERENCE_AUDIO,
        "reference_text": settings.VOICE_REFERENCE_TEXT,
        "whisper_model": settings.WHISPER_MODEL,
        "whisper_device": settings.WHISPER_DEVICE,
        "parallel_workers": async_worker.get_active_workers_summary()
    }

@app.post("/api/chat")
async def chat_endpoint(req: TextChatRequest, background_tasks: BackgroundTasks):
    try:
        response_text, action_type = await router.process_user_input(req.text)
        background_tasks.add_task(synthesize_and_play_audio, response_text)
        
        return {
            "user_text": req.text,
            "response_text": response_text,
            "action_type": action_type,
            "status": "processing_audio_in_background",
            "parallel_workers": async_worker.get_active_workers_summary()
        }
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vision/analyze")
async def vision_analyze_endpoint(req: VisionAnalyzeRequest, background_tasks: BackgroundTasks):
    """Analyze uploaded image or live webcam snapshot."""
    try:
        res_text = await vision_tool.analyze_image_base64(req.image_base64, req.prompt or "Describe what you see.")
        memory.save_message("user", "[Uploaded Image / Webcam Snapshot]")
        memory.save_message("assistant", res_text)
        
        background_tasks.add_task(synthesize_and_play_audio, res_text)
        return {
            "user_text": "[Image Captured]",
            "response_text": res_text,
            "action_type": "tool:vision"
        }
    except Exception as e:
        logger.error(f"Vision analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/process")
async def process_voice_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        temp_path = os.path.join(settings.DATA_DIR, "temp_recording.wav")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        transcript, _ = whisper.transcribe(temp_path)
        if not transcript.strip():
            return {"user_transcript": "", "response_text": "I didn't catch that, Sir.", "action_type": "stt:empty"}

        response_text, action_type = await router.process_user_input(transcript)
        background_tasks.add_task(synthesize_and_play_audio, response_text)

        return {
            "user_transcript": transcript,
            "response_text": response_text,
            "action_type": action_type
        }
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def synthesize_and_play_audio(text: str):
    try:
        playback.set_status("SPEAKING")
        clean_text = text.replace("*", "").replace("`", "").strip()
        provider = tts_factory.get_provider()
        audio_bytes = await provider.synthesize(clean_text)
        
        if audio_bytes:
            out_path = os.path.join(settings.DATA_DIR, "output.wav")
            with open(out_path, "wb") as f:
                f.write(audio_bytes)
            await playback.play_audio(out_path)
    except Exception as e:
        logger.error(f"Background audio synthesis error: {e}")
    finally:
        playback.set_status("IDLE")

@app.post("/api/agent/interrupt")
async def interrupt_agent():
    playback.stop_audio()
    return {"status": "interrupted"}

@app.get("/api/voices")
async def get_voices():
    voices_dir = getattr(settings, 'VOICES_DIR', os.path.join(settings.BASE_DIR, "voices"))
    voices = [f for f in os.listdir(voices_dir) if f.endswith('.wav')]
    return {"voices": voices, "active": os.path.basename(settings.VOICE_REFERENCE_AUDIO)}

@app.post("/api/voices/upload")
async def upload_voice(file: UploadFile = File(...)):
    filename = file.filename or "uploaded_voice.wav"
    voices_dir = getattr(settings, 'VOICES_DIR', os.path.join(settings.BASE_DIR, "voices"))
    dest_path = os.path.join(voices_dir, filename)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    settings.VOICE_REFERENCE_AUDIO = f"voices/{filename}"
    return {"status": "uploaded", "filename": filename}

@app.post("/api/voices/select")
async def select_voice(filename: str = Form(...)):
    path = f"voices/{filename}"
    full_path = os.path.join(settings.BASE_DIR, path)
    if os.path.exists(full_path):
        settings.VOICE_REFERENCE_AUDIO = path
        return {"status": "selected", "active": path}
    raise HTTPException(status_code=400, detail="Voice file not found")

@app.get("/api/voices/preview")
async def preview_voice():
    provider = tts_factory.get_provider()
    audio_bytes = await provider.synthesize("Hello Sir! This is a voice preview of your active voice profile.")
    if audio_bytes:
        out_path = os.path.join(settings.DATA_DIR, "preview.wav")
        with open(out_path, "wb") as f:
            f.write(audio_bytes)
        return FileResponse(out_path, media_type="audio/wav")
    raise HTTPException(status_code=500, detail="Voice preview failed")

@app.post("/api/config")
async def update_config(req: ConfigUpdateRequest):
    if req.ollama_model: settings.OLLAMA_MODEL = req.ollama_model
    if req.tts_provider: settings.TTS_PROVIDER = req.tts_provider
    if req.voice_reference_audio: settings.VOICE_REFERENCE_AUDIO = req.voice_reference_audio
    if req.voice_reference_text: settings.VOICE_REFERENCE_TEXT = req.voice_reference_text
    return {"status": "updated"}
