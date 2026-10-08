import json
import subprocess
from pathlib import Path


ENGINE_DIR = Path(__file__).parent
ENGINE_PATH = ENGINE_DIR / "detector.exe"


def detect_language(message: str):

    process = subprocess.run(
        [str(ENGINE_PATH)],
        input=message + "\n",
        text=True,
        capture_output=True,
        cwd=ENGINE_DIR,
        check=True,
    )

    lines = process.stdout.strip().splitlines()

    for line in reversed(lines):

        start = line.find("{")

        if start == -1:
            continue

        json_text = line[start:]

        try:
            return json.loads(json_text)

        except json.JSONDecodeError:
            continue

    raise RuntimeError(
        "Language engine did not return valid JSON."
    )


if __name__ == "__main__":

    result = detect_language(
        "unsa imong gibuhat"
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )