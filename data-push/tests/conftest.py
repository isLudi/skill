"""Test-time process boundary: a missed mock must never invoke a real CLI/API."""
from unittest.mock import patch
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


@pytest.fixture(autouse=True)
def offline_process_boundary():
    with patch("subprocess.run", side_effect=AssertionError("Tests must mock external subprocess/API calls")):
        yield
