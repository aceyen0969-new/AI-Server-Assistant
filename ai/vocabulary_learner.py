import json
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from ai.learning_candidates import record_candidate


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

TRAINING_DIR = (
    BASE_DIR
    / "language_engine"
    / "training"
)

LEARNED_DIR = (
    TRAINING_DIR
    / "learned"
)

LANGUAGE_FILES = {
    "english": LEARNED_DIR / "english.txt",
    "filipino": LEARNED_DIR / "filipino.txt",
    "bisaya": LEARNED_DIR / "bisaya.txt",
}

MODEL = "openai/gpt-oss-120b"

SUPPORTED_LANGUAGES = {
    "english",
    "filipino",
    "bisaya",
    "unknown",
}

LEARNING_CONFIDENCE = 0.95


def classify_word(
    word: str,
) -> dict:

    word = word.strip().lower()

    if not word:
        return {
            "word": word,
            "language": "unknown",
            "confidence": 0.0,
        }

    api_key = os.getenv(
        "GROQ_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing."
        )

    client = Groq(
        api_key=api_key
    )

    prompt = f"""
Classify this word for a multilingual language detector.

Word:
{word}

Possible languages:
- english
- filipino
- bisaya
- unknown

Rules:
- Return only valid JSON.
- Do not guess when uncertain.
- Consider common vocabulary and normal usage.
- Do not classify names, usernames, abbreviations, random strings, or obvious typos as language words.
- Prefer "unknown" when the word is genuinely uncertain.
- Confidence must be between 0 and 1.
- The language must be exactly one of the allowed languages.

Return exactly:

{{
  "word": "{word}",
  "language": "unknown",
  "confidence": 0.0
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
        response_format={
            "type": "json_object"
        },
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    result = json.loads(
        content
    )

    result_word = str(
        result.get(
            "word",
            word,
        )
    ).strip().lower()

    language = str(
        result.get(
            "language",
            "unknown",
        )
    ).strip().lower()

    try:
        confidence = float(
            result.get(
                "confidence",
                0.0,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        confidence = 0.0

    if result_word != word:
        result_word = word

    if language not in SUPPORTED_LANGUAGES:
        language = "unknown"

    if confidence < 0.0:
        confidence = 0.0

    if confidence > 1.0:
        confidence = 1.0

    return {
        "word": result_word,
        "language": language,
        "confidence": confidence,
    }


def add_word(
    word: str,
    language: str,
) -> bool:

    word = word.strip().lower()

    if not word:
        return False

    if language not in LANGUAGE_FILES:
        return False

    LEARNED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = LANGUAGE_FILES[
        language
    ]

    existing_words = set()

    if path.exists():
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                existing_word = (
                    line.strip()
                    .lower()
                )

                if existing_word:
                    existing_words.add(
                        existing_word
                    )

    if word in existing_words:
        return False

    with path.open(
        "a",
        encoding="utf-8",
    ) as file:

        file.write(
            word + "\n"
        )

    return True


def learn_word(
    word: str,
) -> dict:

    word = word.strip().lower()

    result = classify_word(
        word
    )

    language = result[
        "language"
    ]

    confidence = result[
        "confidence"
    ]

    if (
        language not in LANGUAGE_FILES
        or confidence < LEARNING_CONFIDENCE
    ):
        return {
            "word": word,
            "language": language,
            "confidence": confidence,
            "learned": False,
            "confirmed": False,
        }

    candidate = record_candidate(
        word,
        language,
        confidence,
    )

    confirmed = candidate[
        "confirmed"
    ]

    learned = False

    if confirmed:
        learned = add_word(
            word,
            language,
        )

    return {
        "word": word,
        "language": language,
        "confidence": confidence,
        "learned": learned,
        "confirmed": confirmed,
        "confirmations": candidate[
            "confirmations"
        ],
        "average_confidence": candidate[
            "average_confidence"
        ],
    }