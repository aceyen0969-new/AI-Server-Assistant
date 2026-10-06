import asyncio
import re
import time

from ai.providers import (
    ask_gemini,
    ask_claude,
    ask_openrouter,
    ask_groq
)

from ai.health import (
    mark_success,
    mark_failure,
    is_available
)


# =========================================================
# PROVIDERS
# =========================================================

PROVIDERS = [
    ("Gemini", ask_gemini),
    ("Claude", ask_claude),
    ("OpenRouter", ask_openrouter),
    ("Groq", ask_groq)
]


# =========================================================
# PROVIDER TIMEOUTS
# =========================================================

PROVIDER_TIMEOUTS = {
    "Gemini": 5,
    "Claude": 5,
    "OpenRouter": 8,
    "Groq": 10
}


# =========================================================
# GEMINI QUOTA
# =========================================================

gemini_quota_reset_time = 0


# =========================================================
# EXTRACT RETRY TIME
# =========================================================

def extract_retry_seconds(error_text):

    match = re.search(
        r"retryDelay['\"]?\s*:\s*['\"]?(\d+)s",
        error_text
    )

    if match:
        return int(match.group(1))

    return None


# =========================================================
# BUILD CONVERSATION PROMPT
# =========================================================

def build_prompt(prompt, history):

    if not history:
        return prompt

    conversation_lines = []

    for message in history:

        role = message["role"]
        content = message["content"]

        if role == "user":

            conversation_lines.append(
                f"USER:\n{content}"
            )

        elif role == "assistant":

            conversation_lines.append(
                f"ASSISTANT:\n{content}"
            )

    conversation = "\n\n".join(
        conversation_lines
    )

    return f"""
{prompt}

PREVIOUS CONVERSATION
---------------------
{conversation}

IMPORTANT:
Use the previous conversation to understand references
such as "it", "that", "those", "the channels", "the role",
"what about that", and similar follow-up questions.

The previous conversation may have been answered by
a different AI provider.
Continue the conversation naturally as if you have been
the same assistant throughout.
"""


# =========================================================
# ASK AI
# =========================================================

async def ask_ai(prompt, history=None):

    global gemini_quota_reset_time

    if history is None:
        history = []

    full_prompt = build_prompt(
        prompt,
        history
    )


    # =====================================================
    # CHECK GEMINI QUOTA
    # =====================================================

    if gemini_quota_reset_time > 0:

        remaining = (
            gemini_quota_reset_time
            - time.time()
        )

        if remaining > 0:

            total_seconds = int(
                remaining
            )

            hours = total_seconds // 3600

            minutes = (
                total_seconds % 3600
            ) // 60

            seconds = (
                total_seconds % 60
            )

            print("----------------------------------------")
            print(
                "⏭️ Skipping Gemini because "
                "its quota is exhausted."
            )

            print(
                f"⏳ Gemini quota reset in "
                f"{hours}h {minutes}m {seconds}s"
            )

            print("----------------------------------------")

        else:

            gemini_quota_reset_time = 0


    # =====================================================
    # TRY PROVIDERS
    # =====================================================

    errors = []

    for provider_name, provider_function in PROVIDERS:

        # -------------------------------------------------
        # CHECK HEALTH
        # -------------------------------------------------

        if not is_available(provider_name):

            print("----------------------------------------")
            print(
                f"⏭️ Skipping {provider_name} "
                f"because it is unavailable."
            )

            print("----------------------------------------")

            continue


        print("----------------------------------------")
        print(
            f"🤖 Trying {provider_name}..."
        )


        # -------------------------------------------------
        # GET PROVIDER TIMEOUT
        # -------------------------------------------------

        timeout = PROVIDER_TIMEOUTS.get(
            provider_name,
            5
        )

        print(
            f"⏱️ Timeout: {timeout} seconds"
        )


        # -------------------------------------------------
        # CALL PROVIDER
        # -------------------------------------------------

        try:

            answer = await asyncio.wait_for(
                provider_function(full_prompt),
                timeout=timeout
            )


            if not answer:

                raise RuntimeError(
                    f"{provider_name} returned "
                    f"an empty response."
                )


            # ---------------------------------------------
            # SUCCESS
            # ---------------------------------------------

            mark_success(
                provider_name
            )

            print(
                f"✅ {provider_name} "
                f"responded successfully."
            )

            print("----------------------------------------")


            return {
                "answer": answer,
                "provider": provider_name
            }


        # -------------------------------------------------
        # TIMEOUT
        # -------------------------------------------------

        except asyncio.TimeoutError:

            error_text = (
                f"{provider_name} timed out "
                f"after {timeout} seconds."
            )

            errors.append(
                error_text
            )

            print(
                f"⏱️ {error_text}"
            )

            mark_failure(
                provider_name,
                30
            )

            print(
                "➡️ Trying next provider..."
            )


        # -------------------------------------------------
        # FAILURE
        # -------------------------------------------------

        except Exception as e:

            error_text = str(e)

            errors.append(
                f"{provider_name}: {error_text}"
            )


            print(
                f"❌ {provider_name} failed."
            )

            print(
                f"Error: {error_text}"
            )


            # ---------------------------------------------
            # RETRY TIME
            # ---------------------------------------------

            retry_seconds = extract_retry_seconds(
                error_text
            )


            # ---------------------------------------------
            # MARK PROVIDER UNAVAILABLE
            # ---------------------------------------------

            mark_failure(
                provider_name,
                retry_seconds
            )


            # ---------------------------------------------
            # GEMINI QUOTA
            # ---------------------------------------------

            if provider_name == "Gemini":

                if retry_seconds:

                    gemini_quota_reset_time = (
                        time.time()
                        + retry_seconds
                    )

                    print(
                        "⏭️ Gemini will be skipped "
                        "until its quota resets."
                    )


            print(
                "➡️ Trying next provider..."
            )


    # =====================================================
    # ALL PROVIDERS FAILED
    # =====================================================

    print("----------------------------------------")
    print("❌ ALL AI PROVIDERS FAILED")
    print("----------------------------------------")


    return {
        "answer": None,
        "provider": None,
        "errors": errors
    }