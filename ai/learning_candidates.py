import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

CANDIDATE_FILE = (
    BASE_DIR
    / "language_engine"
    / "training"
    / "learned"
    / "candidates.json"
)

REQUIRED_CONFIRMATIONS = 3


def load_candidates() -> dict:
    if not CANDIDATE_FILE.exists():
        return {}

    try:
        with CANDIDATE_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

    except (
        OSError,
        json.JSONDecodeError,
    ):
        pass

    return {}


def save_candidates(
    candidates: dict,
):
    CANDIDATE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with CANDIDATE_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            candidates,
            file,
            indent=2,
            ensure_ascii=False,
        )


def record_candidate(
    word: str,
    language: str,
    confidence: float,
) -> dict:

    word = word.strip().lower()
    language = language.strip().lower()

    candidates = load_candidates()

    if word not in candidates:
        candidates[word] = {
            "language": language,
            "confirmations": 1,
            "confidence_total": confidence,
        }

    else:
        candidate = candidates[word]

        if candidate.get(
            "language"
        ) == language:

            candidate["confirmations"] = (
                candidate.get(
                    "confirmations",
                    0,
                ) + 1
            )

            candidate["confidence_total"] = (
                candidate.get(
                    "confidence_total",
                    0.0,
                ) + confidence
            )

        else:
            candidates[word] = {
                "language": language,
                "confirmations": 1,
                "confidence_total": confidence,
            }

    candidate = candidates[word]

    confirmations = candidate.get(
        "confirmations",
        0,
    )

    confidence_total = candidate.get(
        "confidence_total",
        0.0,
    )

    average_confidence = (
        confidence_total
        / confirmations
        if confirmations > 0
        else 0.0
    )

    save_candidates(
        candidates
    )

    return {
        "word": word,
        "language": candidate.get(
            "language",
            "unknown",
        ),
        "confirmations": confirmations,
        "average_confidence": average_confidence,
        "confirmed": (
            confirmations
            >= REQUIRED_CONFIRMATIONS
        ),
    }