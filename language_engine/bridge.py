import json
import os
import subprocess
from pathlib import Path


ENGINE_DIR = Path(__file__).parent
ENGINE_NAME = "detector.exe" if os.name == "nt" else "detector"
ENGINE_PATH = ENGINE_DIR / ENGINE_NAME


def detect_language(message: str):
    if not ENGINE_PATH.is_file():
        raise FileNotFoundError(
            f"Language engine not found: {ENGINE_PATH}"
        )

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
        "Language engine did not return valid JSON."
    )


if __name__ == "__main__":
    result = detect_language("unsa imong gibuhat")
    print(json.dumps(result, indent=2))