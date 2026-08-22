import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent import memory

def test_sqlite_memory_operations():
    memory.clear_all_memory()

    # Store preference
    res = memory.remember_fact("preferred language", "Hindi")
    assert "Remembered" in res

    # Recall facts
    facts = memory.recall_facts()
    assert len(facts) == 1
    assert facts[0][0] == "preferred language"
    assert facts[0][1] == "Hindi"

    # Save conversation turn
    memory.save_message("user", "Hello agent")
    memory.save_message("assistant", "Namaste!")
    history = memory.get_recent_history(limit=5)
    assert len(history) == 2
    assert history[0]["content"] == "Hello agent"

    # Forget fact
    res_forget = memory.forget_fact("preferred language")
    assert "Forgot" in res_forget
    assert len(memory.recall_facts()) == 0

if __name__ == "__main__":
    test_sqlite_memory_operations()
    print("[OK] SQLite Memory Tests Passed")
