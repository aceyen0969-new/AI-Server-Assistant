import json
import os
import subprocess
from pathlib import Path

from ai.vocabulary_learner import learn_word


ENGINE_DIR = Path(__file__).parent
ENGINE_NAME = "detector.exe" if os.name == "nt" else "detector"
ENGINE_PATH = ENGINE_DIR / ENGINE_NAME

MAX_UNKNOWN_WORDS = 3


def detect_message(message: str):
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

    output = process.stdout
    start = output.find("{")
    end = output.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise RuntimeError(
            "Language engine returned no valid JSON."
        )

    try:
        return json.loads(output[start:end + 1])
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Language engine returned invalid JSON."
        ) from error


def learn_unknown_words(detection_result: dict) -> list[dict]:
    unknown_words = detection_result.get("unknown_words", [])

    if not isinstance(unknown_words, list):
        return []

    results = []

    for word in unknown_words[:MAX_UNKNOWN_WORDS]:
        if not isinstance(word, str):
            continue

        word = word.strip().lower()

        if not word:
            continue

        try:
            results.append(learn_word(word))
        except Exception as error:
            results.append({
                "word": word,
                "language": "unknown",
                "confidence": 0.0,
                "learned": False,
                "error": str(error),
            })

    return results