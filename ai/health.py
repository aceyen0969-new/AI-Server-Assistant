import time


providers = {
    "Gemini": {
        "status": "unknown",
        "available": False,
        "retry_at": 0
    },
    "Claude": {
        "status": "unknown",
        "available": False,
        "retry_at": 0
    },
    "OpenRouter": {
        "status": "unknown",
        "available": False,
        "retry_at": 0
    },
    "Groq": {
        "status": "unknown",
        "available": False,
        "retry_at": 0
    }
}


def mark_success(provider_name):
    if provider_name not in providers:
        return

    providers[provider_name]["status"] = "online"
    providers[provider_name]["available"] = True
    providers[provider_name]["retry_at"] = 0


def mark_failure(provider_name, retry_seconds=None):
    if provider_name not in providers:
        return

    providers[provider_name]["status"] = "offline"
    providers[provider_name]["available"] = False

    if retry_seconds is not None and retry_seconds > 0:
        providers[provider_name]["retry_at"] = (
            time.time() + retry_seconds
        )
    else:
        providers[provider_name]["retry_at"] = 0


def is_available(provider_name):
    if provider_name not in providers:
        return False

    provider = providers[provider_name]

    if provider["status"] == "unknown":
        return True

    retry_at = provider["retry_at"]

    if retry_at > 0:
        if time.time() >= retry_at:
            provider["status"] = "unknown"
            provider["available"] = False
            provider["retry_at"] = 0
            return True

        return False

    return provider["available"]


def any_provider_available():
    for provider_name in providers:
        provider = providers[provider_name]

        if provider["status"] == "online":
            if is_available(provider_name):
                return True

    return False


def get_status():
    result = {}

    for provider_name in providers:
        provider = providers[provider_name]

        if (
            provider["retry_at"] > 0
            and time.time() >= provider["retry_at"]
        ):
            provider["status"] = "unknown"
            provider["available"] = False
            provider["retry_at"] = 0

        result[provider_name] = {
            "available": provider["available"],
            "status": provider["status"]
        }

    return result


def get_ai_status():
    if any_provider_available():
        return "online"

    return "offline"