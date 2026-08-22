# OmniVoice — Fully Local Voice AI Agent with Personal Voice Cloning

OmniVoice is a **100% local, free, privacy-first Voice AI Agent** designed for Windows. It provides zero-shot personal voice cloning, local speech recognition, Ollama LLM integration, agentic tool execution, persistent SQLite memory, voice activity detection (VAD), barge-in interruption, and a clean local web interface.

---

## 🏗 System Architecture

```
Microphone
    ↓
VAD (Voice Activity Detection)
    ↓
Faster-Whisper (Local STT - CPU/INT8)
    ↓
Ollama (Local LLM - e.g. qwen3:1.7b)
    ↓
Agent Router
   ├── Local Tools (Calculator, Date/Time, App Launcher, File Search, Web Search)
   └── SQLite Memory (Preferences & Facts)
    ↓
TTS Provider Engine
   ├── OmniVoice (Zero-shot reference audio clone: voices/my_voice.wav)
   ├── Piper TTS (Local CPU fallback)
   └── Edge TTS (Fallback)
    ↓
Speaker (With Barge-In Interrupt Listener)
```

---

## ⚡ Key Features

1. **Zero-Shot Personal Voice Cloning (`OmniVoice`)**:
   - Provide a short `.wav` reference audio sample (e.g., `voices/my_voice.wav`).
   - Generates speech in your own voice without model fine-tuning.
   - Automatically transcribes reference audio using local Whisper if reference text is omitted.

2. **100% Free & Local Execution**:
   - Uses **Faster-Whisper** for STT (INT8 CPU optimized for low-spec PCs).
   - Uses **Ollama** for LLM (`OLLAMA_HOST=http://localhost:11434`).
   - No paid APIs required (OpenAI, ElevenLabs, Deepgram are NOT needed).

3. **Hardware Aware & Low VRAM Compatible**:
   - Designed to run primarily on CPU, making it fully compatible with low-end GPUs (e.g., NVIDIA GeForce GT 710 2GB VRAM).

4. **Agentic Tool Execution**:
   - **Calculator**: Math evaluation (`25 * 48`, `17% of 8500`).
   - **Date & Time**: Real-time date and time queries (`What time is it?`).
   - **Open Application**: Safely launches configured Windows apps (`Open Chrome`, `Open VS Code`, `Open Notepad`).
   - **File Search**: Fast local file matching (`Find my resume`).
   - **Web Search**: Free local search (`Search the web for ...`).

5. **Persistent SQLite Memory**:
   - Remembers facts and preferences (`Remember that my preferred language is Hindi`).
   - Recalls stored information (`What language do I prefer?`).
   - Commands: `Forget that`, `Show my memory`, `Clear my memory`.

6. **Multilingual (English + Hindi / Hinglish)**:
   - Responds naturally to Hinglish inputs (`Bhai kal mujhe 10 baje meeting yaad dila dena`).

7. **Voice Interaction & Barge-In**:
   - Pauses listening while speaking to prevent feedback loop.
   - Barge-in interrupt handling ("stop", "cancel", "shut up").

8. **Local Web Control Panel**:
   - Displays states: `IDLE`, `LISTENING`, `THINKING`, `SPEAKING`, `ERROR`.
   - Voice sample manager (upload/select/preview voice samples).
   - Real-time conversation transcript and tool execution log.

---

## 🚀 Quickstart Guide for Windows

### Prerequisites

1. **Install Python 3.10 or 3.11**: [python.org](https://www.python.org/downloads/)
2. **Install & Run Ollama**: [ollama.com](https://ollama.com)
   ```bash
   # In terminal, pull your preferred model:
   ollama pull qwen3:1.7b
   ```

### Installation

Run the automated Windows setup script:
```cmd
setup.bat
```
`setup.bat` will:
- Check Python installation.
- Create a virtual environment (`venv`).
- Install all dependencies.
- Create default `.env` configuration.
- Check Ollama status.
- Create `voices/` and `data/` directories.

---

## 🎙 Adding Your Personal Voice Sample

1. Place your `.wav` voice recording in the `voices/` directory:
   ```
   voices/my_voice.wav
   ```
2. (Optional) In the Web UI or `.env`, set reference text if desired (`VOICE_REFERENCE_TEXT`). If left blank, local Whisper will automatically transcribe your audio sample.

---

## 🏃 Running the Application

Double click or run:
```cmd
run.bat
```
This launches the server at `http://localhost:8000` and automatically opens your web browser.

Alternatively, to run terminal push-to-talk mode:
```bash
python -m omni_voice.voice_cli
```

---

## 🛠 Configuration Reference (`.env`)

```ini
# Ollama LLM
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3:1.7b

# Faster-Whisper STT
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8

# TTS Provider & Voice Cloning
TTS_PROVIDER=omnivoice
VOICE_REFERENCE_AUDIO=voices/my_voice.wav
VOICE_REFERENCE_TEXT=

# Fallback Settings
PIPER_VOICE=en_US-lessac-medium
EDGE_TTS_VOICE=en-US-AriaNeural

# Interaction
WAKE_WORD_ENABLED=false
PORT=8000
```

---

## 🧪 Running Tests

To verify local tools, memory storage, and agent routing:
```bash
python tests/test_calculator.py
python tests/test_memory.py
python tests/test_router.py
```

---

## 🔒 Privacy & Security Statement

- All audio recordings, transcriptions, LLM prompts, and voice samples remain **100% local on your PC**.
- Zero voice data or telemetry is sent to third-party servers by default.
