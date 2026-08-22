import base64
import httpx
import logging
import os
from typing import Optional
from PIL import Image
import io
from app.config import settings

logger = logging.getLogger(__name__)

async def analyze_image_base64(b64_data: str, prompt: str = "Describe what you see in this image in detail.") -> str:
    """Analyze base64 image using Ollama Vision model (moondream/llava) with PIL fallback."""
    # Clean base64 header if present
    if "," in b64_data:
        b64_data = b64_data.split(",", 1)[1]

    # Try Ollama Vision Model first (moondream / llava)
    vision_models = ["moondream", "llava", "llava:v1.6"]
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Check available models
            res = await client.get(f"{settings.OLLAMA_HOST}/api/tags")
            installed = []
            if res.status_code == 200:
                installed = [m.get("name") for m in res.json().get("models", [])]
            
            selected_model = next((m for m in vision_models if any(v in m for v in installed)), None)
            if not selected_model and installed:
                selected_model = installed[0]

            if selected_model:
                payload = {
                    "model": selected_model,
                    "prompt": prompt,
                    "images": [b64_data],
                    "stream": False
                }
                v_res = await client.post(f"{settings.OLLAMA_HOST}/api/generate", json=payload)
                if v_res.status_code == 200:
                    answer = v_res.json().get("response", "").strip()
                    if answer:
                        return f"Sir, I have analyzed the image using my vision neural engine ({selected_model}):\n\n{answer}"
    except Exception as e:
        logger.warning(f"Ollama Vision API notice ({e}), falling back to PIL image inspection...")

    # PIL Basic Image Analysis Fallback
    try:
        img_bytes = base64.b64decode(b64_data)
        img = Image.open(io.BytesIO(img_bytes))
        width, height = img.size
        mode = img.mode
        return (
            f"Sir, I have captured and inspected the image.\n"
            f"Image Dimensions: {width}x{height} pixels, Color Mode: {mode}.\n"
            "The image has been processed into my visual memory buffer, Sir."
        )
    except Exception as err:
        return f"Sir, I encountered an error processing the visual frame: {str(err)}"

async def analyze_image_file(file_path: str, prompt: str = "Describe what you see in this image.") -> str:
    """Analyze image file from disk."""
    if not os.path.exists(file_path):
        return f"Sir, the image file '{file_path}' does not exist."
    try:
        with open(file_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")
        return await analyze_image_base64(b64_data, prompt)
    except Exception as e:
        return f"Sir, error reading image file '{file_path}': {str(e)}"
