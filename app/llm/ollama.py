import re
import httpx
import logging
from typing import List, Dict, Tuple, Optional
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are J.A.R.V.I.S., a highly intelligent, polite, local Voice AI assistant. "
    "STRICT SCRIPT MANDATE: You MUST write ALL responses using ONLY the English/Roman alphabet (A-Z, a-z). "
    "NEVER write in Devanagari script (hindi characters). Always write in Hinglish (Roman Hindi) or English. "
    "Example: 'Sab badhiya hai Sir! Aap bataiye aaj main aapki kya help karun?' "
    "Do NOT use markdown formatting, bullet points, asterisks (*), or code blocks in normal speech."
)

def remove_devanagari(text: str) -> str:
    """Remove or replace any Devanagari script characters with Roman script."""
    # Check if text contains Devanagari characters (\u0900-\u097F)
    if re.search(r"[\u0900-\u097F]", text):
        logger.warning("Detected Devanagari script in output. Filtering out Devanagari text...")
        # Strip out Devanagari script characters
        cleaned = re.sub(r"[\u0900-\u097F]+", "", text).strip()
        if not cleaned:
            return "Sab badhiya hai Sir! Aap bataiye main aapki kya help karun?"
        return cleaned
    return text

def clean_repetitive_response(text: str) -> str:
    """Clean repetitive lines and remove hallucinated loops."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    seen = set()
    deduped = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            deduped.append(line)
    result = '\n'.join(deduped).strip()
    result = remove_devanagari(result)
    return result if result else "Sab badhiya hai Sir! How may I assist you today?"

async def check_ollama_status() -> Tuple[bool, str]:
    """Check if Ollama server is running and accessible."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(f"{settings.OLLAMA_HOST}/api/tags")
            if res.status_code == 200:
                return True, "Ollama is running."
            return False, f"Ollama returned status code {res.status_code}."
    except Exception as e:
        return False, "Could not connect to Ollama. Run: ollama serve"

async def get_available_models() -> List[str]:
    """Get list of models installed on Ollama."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(f"{settings.OLLAMA_HOST}/api/tags")
            if res.status_code == 200:
                models = res.json().get("models", [])
                names = [m.get("name") for m in models if m.get("name")]
                return names
    except Exception as e:
        logger.warning(f"Error fetching installed models: {e}")
    return []

async def generate_response(prompt: str, history: Optional[List[Dict[str, str]]] = None, system_prompt: str = SYSTEM_PROMPT) -> str:
    """Generate response from local Ollama LLM model."""
    is_running, error_msg = await check_ollama_status()

    if not is_running:
        return f"Sir, {error_msg}"

    installed_models = await get_available_models()
    target_model = settings.OLLAMA_MODEL

    if installed_models and target_model not in installed_models:
        matched = next((m for m in installed_models if target_model.split(":")[0] in m), None)
        target_model = matched or installed_models[0]
        logger.info(f"Resolved model to '{target_model}'")

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": target_model,
        "messages": messages,
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(f"{settings.OLLAMA_HOST}/api/chat", json=payload)
            if res.status_code == 200:
                data = res.json()
                content = data.get("message", {}).get("content", "").strip()
                if content:
                    return clean_repetitive_response(content)
            logger.error(f"Ollama returned error {res.status_code}: {res.text}")
            return f"Sir, Ollama error ({res.status_code})."
    except Exception as e:
        logger.error(f"Error calling Ollama API: {e}")
        return f"Sir, I encountered an issue communicating with Ollama: {str(e)}"
