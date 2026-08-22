import re
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

async def scrape_url(url: str, max_chars: int = 1500) -> str:
    """Multi-engine web scraper using Crawl4AI, Scrapling, Firecrawl, and HTTP fallback."""
    clean_url = url.strip()
    if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
        clean_url = "https://" + clean_url

    logger.info(f"Initiating web scrape for URL: {clean_url}")

    # Engine 1: Crawl4AI
    try:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(url=clean_url)
            if result and result.markdown:
                content = result.markdown.strip()
                if len(content) > max_chars:
                    content = content[:max_chars] + "\n...[truncated]"
                return f"[Engine: Crawl4AI] Content from {clean_url}:\n\n{content}"
    except Exception as e:
        logger.warning(f"Crawl4AI engine note ({e}), trying Scrapling...")

    # Engine 2: Scrapling (Anti-bot parser)
    try:
        from app.tools.advanced_skills import scrape_with_scrapling
        res = await scrape_with_scrapling(clean_url, max_chars)
        if res and "error" not in res.lower():
            return f"[Engine: Scrapling]\n{res}"
    except Exception as e:
        logger.warning(f"Scrapling engine note ({e}), trying Firecrawl...")

    # Engine 3: Firecrawl
    try:
        from firecrawl import FirecrawlApp
        app = FirecrawlApp()
        res = app.scrape_url(clean_url, params={'formats': ['markdown']})
        if res and 'markdown' in res:
            text = res['markdown'][:max_chars]
            return f"[Engine: Firecrawl] Content from {clean_url}:\n\n{text}"
    except Exception as e:
        logger.warning(f"Firecrawl engine note ({e}), using HTTP fallback...")

    # Engine 4: Standard HTTP Text Extractor
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(clean_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            if resp.status_code == 200:
                html = resp.text
                text = re.sub(r"<(script|style).*?>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
                if len(text) > max_chars:
                    text = text[:max_chars] + "\n...[truncated]"
                return f"[Engine: HTTP Parser] Content from {clean_url}:\n\n{text}"
            return f"Failed to scrape {clean_url}. Server returned HTTP {resp.status_code}."
    except Exception as err:
        logger.error(f"Scraper error: {err}")
        return f"Could not scrape {clean_url}: {str(err)}"
