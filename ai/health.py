import time


# =========================================================
# PROVIDER HEALTH
# =========================================================

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


# =========================================================
# MARK PROVIDER SUCCESS
# =========================================================

def mark_success(provider_name):

    if provider_name not in providers:
        return

    providers[provider_name]["status"] = "online"

    providers[provider_name]["available"] = True

    providers[provider_name]["retry_at"] = 0


# =========================================================
# MARK PROVIDER FAILURE
# =========================================================

def mark_failure(
    provider_name,
    retry_seconds=None
):

    if provider_name not in providers:
        return

    providers[provider_name]["status"] = "offline"

    providers[provider_name]["available"] = False


    if retry_seconds:

        providers[provider_name]["retry_at"] = (
            time.time() + retry_seconds
        )

    else:

        providers[provider_name]["retry_at"] = 0


# =========================================================
# CHECK IF PROVIDER CAN BE TRIED
# =========================================================

def is_available(provider_name):

    if provider_name not in providers:
        return False

    provider = providers[provider_name]


    # -----------------------------------------------------
    # UNKNOWN
    # -----------------------------------------------------
    # The provider has not been tested yet.
    #
    # UNKNOWN means:
    #
    # "We don't know if it works."
    #
    # Therefore, allow the manager to try it.
    # -----------------------------------------------------

    if provider["status"] == "unknown":

        return True


    # -----------------------------------------------------
    # RETRY TIMER
    # -----------------------------------------------------

    retry_at = provider["retry_at"]


    if retry_at > 0:

        # -------------------------------------------------
        # RETRY TIME HAS EXPIRED
        # -------------------------------------------------

        if time.time() >= retry_at:

            provider["status"] = "unknown"

            provider["available"] = False

            provider["retry_at"] = 0

            # Allow the provider to be tested again.

            return True


        # -------------------------------------------------
        # STILL WAITING
        # -------------------------------------------------

        return False


    # -----------------------------------------------------
    # NORMAL STATUS
    # -----------------------------------------------------

    return provider["available"]


# =========================================================
# CHECK IF ANY PROVIDER IS ACTUALLY ONLINE
# =========================================================

def any_provider_available():

    for provider_name in providers:

        provider = providers[provider_name]


        # -------------------------------------------------
        # ONLY ONLINE PROVIDERS COUNT
        # -------------------------------------------------
        # UNKNOWN providers can be tested, but they should
        # NOT make the overall AI status appear online.
        # -------------------------------------------------

        if provider["status"] == "online":

            if is_available(provider_name):

                return True


    return False


# =========================================================
# GET CURRENT PROVIDER STATUS
# =========================================================

def get_status():

    result = {}


    for provider_name in providers:

        provider = providers[provider_name]


        # -------------------------------------------------
        # CHECK EXPIRED RETRY TIMER
        # -------------------------------------------------

        if (
            provider["retry_at"] > 0
            and time.time() >= provider["retry_at"]
        ):

            provider["status"] = "unknown"

            provider["available"] = False

            provider["retry_at"] = 0


        # -------------------------------------------------
        # SAVE STATUS
        # -------------------------------------------------

        result[provider_name] = {

            "available": provider["available"],

            "status": provider["status"]

        }


    return result


# =========================================================
# GET OVERALL AI STATUS
# =========================================================

def get_ai_status():

    if any_provider_available():

        return "online"


    return "offline"