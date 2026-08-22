import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent import router
from app.tools import advanced_skills, web_scraper

async def test_all_added_skills():
    # 1. GitHub repo inspection test
    reply, action = await router.process_user_input("Inspect repo https://github.com/unclecode/crawl4ai")
    assert "crawl4ai" in reply.lower()
    assert action == "tool:github"

    # 2. Scrapling / Web Scraper test
    reply, action = await router.process_user_input("Scrape https://github.com/D4Vinci/Scrapling")
    assert "scrapling" in reply.lower() or "content" in reply.lower()
    assert action == "tool:web_scraper"

    # 3. Playwright browser automation test
    reply, action = await router.process_user_input("Playwright browse https://python.org")
    assert "python" in reply.lower() or "playwright" in reply.lower()
    assert action == "tool:playwright"

    # 4. Design & UI Taste Skill test
    reply, action = await router.process_user_input("UI design review for Dashboard Navbar")
    assert "micro-interactions" in reply.lower() or "taste" in reply.lower()
    assert action == "tool:ui_design"

    # 5. Strix Security Audit skill test
    reply, action = await router.process_user_input("Strix security scan for my application")
    assert "strix" in reply.lower() or "vulnerabilities" in reply.lower()
    assert action == "tool:security_strix"

if __name__ == "__main__":
    asyncio.run(test_all_added_skills())
    print("[OK] All Integrated Skills Tests Passed Successfully!")
