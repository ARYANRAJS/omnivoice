import asyncio
import logging
import time
from typing import Callable, Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Registry of active and completed parallel workers
active_workers: Dict[str, Dict[str, Any]] = {}
completed_worker_results: List[Dict[str, Any]] = []

def register_worker(worker_id: str, description: str, coro_func: Callable, *args, **kwargs) -> asyncio.Task:
    """Register and launch a parallel background task immediately."""
    worker_id_unique = f"{worker_id}_{int(time.time()*1000)}"
    
    info = {
        "id": worker_id_unique,
        "name": worker_id,
        "description": description,
        "status": "RUNNING",
        "start_time": time.time(),
        "result": None,
        "error": None
    }
    active_workers[worker_id_unique] = info

    async def _runner():
        try:
            logger.info(f"⚡ [PARALLEL WORKER START] {worker_id_unique}: {description}")
            res = await coro_func(*args, **kwargs) if asyncio.iscoroutinefunction(coro_func) else coro_func(*args, **kwargs)
            info["status"] = "COMPLETED"
            info["result"] = res
            completed_worker_results.append(info)
            logger.info(f"✓ [PARALLEL WORKER DONE] {worker_id_unique}")
        except Exception as e:
            logger.error(f"❌ [PARALLEL WORKER ERROR] {worker_id_unique}: {e}")
            info["status"] = "FAILED"
            info["error"] = str(e)
            completed_worker_results.append(info)
        finally:
            active_workers.pop(worker_id_unique, None)

    task = asyncio.create_task(_runner())
    return task

def get_active_workers_summary() -> List[Dict[str, Any]]:
    """Return status of all running parallel workers."""
    summary = []
    for wid, info in active_workers.items():
        summary.append({
            "id": wid,
            "name": info["name"],
            "description": info["description"],
            "status": info["status"],
            "elapsed_sec": round(time.time() - info["start_time"], 1)
        })
    return summary

def pop_completed_notification() -> Optional[str]:
    """Retrieve and clear finished background notifications for J.A.R.V.I.S. speech."""
    if not completed_worker_results:
        return None
    
    info = completed_worker_results.pop(0)
    name = info.get("name", "background task")
    desc = info.get("description", "")
    if info["status"] == "COMPLETED":
        return f"Sir, your parallel worker for '{desc or name}' has completed. Would you like me to present the results?"
    return f"Sir, your parallel worker for '{desc or name}' encountered an issue: {info.get('error')}."
