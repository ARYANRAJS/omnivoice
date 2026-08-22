import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent import router, graph_memory
from app.tools import web_scraper

async def test_jarvis_skills():
    # Test behavior graph logging
    graph_memory.log_user_behavior("coding", "Prefers PyTorch Geometric for graph neural networks")
    graph_memory.add_graph_relation("user", "uses", "pytorch_geometric")
    profile = graph_memory.query_user_profile()
    assert len(profile["behaviors"]) > 0

    # Test Crawl4AI scraper tool
    res = await web_scraper.scrape_url("https://python.org")
    assert "python" in res.lower() or "scraped" in res.lower()

    # Test Router with Jarvis persona
    reply, action = await router.process_user_input("Remember that I use PyTorch Geometric for AI research")
    assert "Sir" in reply or "stored" in reply
    assert action == "tool:memory_store"

if __name__ == "__main__":
    asyncio.run(test_jarvis_skills())
    print("[OK] Jarvis Skills & Crawl4AI Tests Passed")
