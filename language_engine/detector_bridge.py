import json
import subprocess
from pathlib import Path

from ai.vocabulary_learner import learn_word


ENGINE_DIR = Path(__file__).parent
ENGINE_PATH = ENGINE_DIR / "detector.exe"

MAX_UNKNOWN_WORDS = 3


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


def learn_unknown_words(
    detection_result: dict,
) -> list[dict]:

    unknown_words = detection_result.get(
        "unknown_words",
        [],
    )

    if not isinstance(
        unknown_words,
        list,
    ):
        return []

    results = []

    for word in unknown_words[
        :MAX_UNKNOWN_WORDS
    ]:
        if not isinstance(
            word,
            str,
        ):
            continue

        word = word.strip().lower()

        if not word:
            continue

        try:
            result = learn_word(
                word
            )

            results.append(
                result
            )

        except Exception as error:
            results.append(
                {
                    "word": word,
                    "language": "unknown",
                    "confidence": 0.0,
                    "learned": False,
                    "error": str(error),
                }
            )

    return results