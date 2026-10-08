import json
import subprocess
from pathlib import Path


ENGINE_DIR = Path(__file__).parent
ENGINE_PATH = ENGINE_DIR / "detector.exe"


def detect_message(
    message: str,
):
    process = subprocess.run(
        [str(ENGINE_PATH)],
        input=message + "\n",
        text=True,
        capture_output=True,
        cwd=ENGINE_DIR,
        check=True,
    )

    output = process.stdout

    start = output.find("{")
    end = output.rfind("}")

    if (
        start == -1
        or end == -1
        or end <= start
    ):
        raise RuntimeError(
            "Language engine returned no valid JSON."
        )

    json_text = output[
        start:end + 1
    ]

    try:
        return json.loads(
            json_text
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Language engine returned invalid JSON."
        ) from error