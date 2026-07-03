from __future__ import annotations

import subprocess
import sys


def test_live_smoke_script_requires_api_key() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/live_smoke_test.py"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--api-key" in result.stderr
