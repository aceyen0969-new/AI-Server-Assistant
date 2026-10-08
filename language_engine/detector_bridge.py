import json
import subprocess
from pathlib import Path


ENGINE_DIR = Path(__file__).parent
ENGINE_PATH = ENGINE_DIR / "detector.exe"


def detect_message(message: str):

    process = subprocess.run(
        [str(ENGINE_PATH)],
        input=message + "\n",
        text=True,
        capture_output=True,
        cwd=ENGINE_DIR,
        check=True,
    )

    for line in reversed(process.stdout.strip().splitlines()):

        start = line.find("{")

        if start == -1:
            continue

        try:
            return json.loads(line[start:])

        except json.JSONDecodeError:
            continue

    raise RuntimeError(
        "Language engine returned no valid JSON."
    )