import logging
from typing import List

logger = logging.getLogger(__name__)

def search_web(query: str, max_results: int = 5) -> str:
    """Perform live web search using DDGS or fallback scraper."""
    clean_q = query.strip()
    if not clean_q:
        return "No query provided for web search."

    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(clean_q, max_results=max_results))
            if results:
                snippets = []
                for r in results:
                    title = r.get("title", "")
                    body = r.get("body", "")
                    href = r.get("href", "")
                    snippets.append(f"Source ({title} - {href}):\n{body}")
                return "Real-Time Web Search Results:\n" + "\n\n".join(snippets)
    except Exception as e:
        logger.warning(f"DDGS web search notice ({e}), attempting fallback scraper...")

    # Fallback to direct HTTP search parser
    try:
        import httpx
        import re
        url = f"https://html.duckduckgo.com/html/?q={clean_q}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            res = client.get(url, headers=headers)
            if res.status_code == 200:
                titles = re.findall(r'<a class="result__a"[^>]*>(.*?)</a>', res.text)
                snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', res.text)
                clean_snippets = []
                for t, s in zip(titles[:max_results], snippets[:max_results]):
                    t_clean = re.sub(r'<[^>]+>', '', t).strip()
                    s_clean = re.sub(r'<[^>]+>', '', s).strip()
                    clean_snippets.append(f"- {t_clean}: {s_clean}")
                if clean_snippets:
                    return "Real-Time Web Search Results:\n" + "\n".join(clean_snippets)
    except Exception as err:
        logger.error(f"Fallback search error: {err}")

    return f"Web search could not be completed for '{clean_q}'."
