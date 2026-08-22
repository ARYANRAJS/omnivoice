import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent import router

async def test_agent_routing():
    # Calculator route
    reply, action = await router.process_user_input("Calculate 25 * 48")
    assert "1200" in reply
    assert action == "tool:calculator"

    # DateTime route
    reply, action = await router.process_user_input("What time is it?")
    assert action == "tool:datetime"

    # Memory store route
    reply, action = await router.process_user_input("Remember that my preferred language is Hindi")
    assert action == "tool:memory_store"

    # Memory query route
    reply, action = await router.process_user_input("What language do I prefer?")
    assert action == "tool:memory_query"
    assert "Hindi" in reply

if __name__ == "__main__":
    asyncio.run(test_agent_routing())
    print("[OK] Agent Routing Tests Passed")
