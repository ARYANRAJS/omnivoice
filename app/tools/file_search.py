import os
from pathlib import Path
from typing import List

def search_files(keyword: str, search_dir: str = None, max_results: int = 5) -> str:
    """Search user directory for files matching keyword."""
    if not search_dir:
        # Default to User home directory (Desktop, Documents, Downloads)
        search_dir = str(Path.home())

    kw = keyword.lower().strip()
    matches: List[str] = []

    try:
        root_path = Path(search_dir)
        if not root_path.exists():
            return f"Directory '{search_dir}' does not exist."

        # Target key folders if searching home to avoid endless indexing
        targets = [root_path / "Desktop", root_path / "Documents", root_path / "Downloads", root_path]
        
        visited_count = 0
        for t in targets:
            if not t.exists() or len(matches) >= max_results:
                continue
            
            for path in t.rglob("*"):
                visited_count += 1
                if visited_count > 1000:
                    break
                if path.is_file() and kw in path.name.lower():
                    matches.append(str(path))
                    if len(matches) >= max_results:
                        break

        if matches:
            res_str = "\n".join([f"- {m}" for m in matches])
            return f"Found {len(matches)} matching file(s):\n{res_str}"
        return f"No files matching '{keyword}' were found in '{search_dir}'."
    except Exception as e:
        return f"Error searching files: {e}"
