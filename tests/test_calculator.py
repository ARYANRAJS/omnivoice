import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.tools.calculator import calculate
from app.tools.datetime_tool import get_current_time, get_current_date

def test_calculator_basic():
    assert "Result: 1200" in calculate("25 * 48")
    assert "Result: 1445" in calculate("17% of 8500")
    assert "Result: 10" in calculate("5 + 5")

def test_datetime():
    t = get_current_time()
    d = get_current_date()
    assert "current time" in t.lower()
    assert "date" in d.lower()

if __name__ == "__main__":
    test_calculator_basic()
    test_datetime()
    print("[OK] Calculator & Datetime Tests Passed")
