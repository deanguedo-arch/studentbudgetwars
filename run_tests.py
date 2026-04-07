import pytest
import sys

with open("test_results.txt", "w", encoding="utf-8") as f:
    sys.stdout = f
    sys.stderr = f
    pytest.main(["-q", "--tb=short"])
