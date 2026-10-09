import re


SIGNAL_PATTERNS = {
    "possible_escalation": [
        r"\b(shut up|fuck off|leave me alone)\b",
        r"\b(i will fight you|come fight me)\b",
        r"\b(tigil ka na|tumahimik ka)\b",
        r"\b(gikapoy na ko nimo|ayaw pagbuot)\b",
    ],
    "de_escalation": [
        r"\b(calm down|stop arguing|stop fighting)\b",
        r"\b(wag kayong mag-away|huwag kayong mag-away)\b",
        r"\b(tigil na kayo|magbati na kayo)\b",
        r"\b(paghunong na|ayaw na mo pag-away)\b",
    ],
    "past_conflict": [
        r"\b(they fought|we fought|they were arguing)\b",
        r"\b(nag-away sila|nag-away kami|nag-away tayo)\b",
        r"\b(nag-away sila ganina|nag-away mi ganina)\b",
    ],
    "conflict_avoidance": [
        r"\b(i don't want to fight|i do not want to fight)\b",
        r"\b(ayoko makipag-away|ayaw ko makig-away)\b",
        r"\b(dili ko gusto makig-away)\b",
    ],
}


def normalize_message(message: str) -> str:
    message = message.lower()
    message = re.sub(r"\s+", " ", message)
    return message.strip()


def find_signals(message: str) -> list[str]:
    normalized = normalize_message(message)
    signals = []

    for signal_type, patterns in SIGNAL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, normalized):
                signals.append(signal_type)
                break

    return signals


def detect_conflict_signals(message: str) -> dict:
    if not isinstance(message, str) or not message.strip():
        return {
            "signals": [],
            "possible_conflict_language": False,
            "assessment": "insufficient_evidence",
        }

    signals = find_signals(message)

    if "de_escalation" in signals:
        assessment = "de_escalation_language"
    elif "conflict_avoidance" in signals:
        assessment = "conflict_avoidance_language"
    elif "past_conflict" in signals:
        assessment = "past_conflict_reference"
    elif "possible_escalation" in signals:
        assessment = "possible_escalation_language"
    else:
        assessment = "no_clear_signal"

    return {
        "signals": signals,
        "possible_conflict_language": bool(signals),
        "assessment": assessment,
    }