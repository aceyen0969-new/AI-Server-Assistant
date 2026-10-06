import re
import time

from ai.providers import (
    ask_gemini,
    ask_openrouter,
    ask_groq
)


# =========================================================
# PROVIDERS
# =========================================================

PROVIDERS = [
    ("Gemini", ask_gemini),
    ("OpenRouter", ask_openrouter),
    ("Groq", ask_groq)
]


# =========================================================
# GEMINI QUOTA MEMORY
# =========================================================

gemini_quota_reset_time = 0


def extract_retry_seconds(error_text):
    """
    Extract Gemini's retryDelay from an error.

    Example:
    retryDelay': '65195s'
    """

    match = re.search(
        r"retryDelay['\"]?\s*:\s*['\"]?(\d+)s",
        error_text
    )

    if match:
        return int(match.group(1))

    return None


def build_prompt(prompt, history):
    """
    Combine the current server context with previous
    conversation messages.

    The AI providers themselves remain stateless.
    The bot supplies the conversation history every time.
    """

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
# MAIN AI FUNCTION
# =========================================================

async def ask_ai(prompt, history=None):

    global gemini_quota_reset_time

    if history is None:
        history = []


    # =====================================================
    # BUILD PROMPT WITH MEMORY
    # =====================================================

    full_prompt = build_prompt(
        prompt,
        history
    )


    # =====================================================
    # CHECK GEMINI QUOTA
    # =====================================================

    providers_to_try = PROVIDERS

    if gemini_quota_reset_time > 0:

        remaining = (
            gemini_quota_reset_time
            - time.time()
        )

        if remaining > 0:

            total_seconds = int(remaining)

            hours = total_seconds // 3600
            minutes = (
                total_seconds % 3600
            ) // 60
            seconds = total_seconds % 60

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

            providers_to_try = [
                provider
                for provider in PROVIDERS
                if provider[0] != "Gemini"
            ]

        else:

            print("----------------------------------------")
            print("🔄 Gemini quota should have reset.")
            print("Trying Gemini again...")
            print("----------------------------------------")

            gemini_quota_reset_time = 0


    # =====================================================
    # TRY PROVIDERS
    # =====================================================

    errors = []

    for provider_name, provider_function in providers_to_try:

        print("----------------------------------------")
        print(
            f"🤖 Trying {provider_name}..."
        )

        try:

            answer = await provider_function(
                full_prompt
            )

            if not answer:
                raise RuntimeError(
                    f"{provider_name} returned an empty response."
                )

            print(
                f"✅ {provider_name} responded successfully."
            )

            print("----------------------------------------")

            return {
                "answer": answer,
                "provider": provider_name
            }


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


            # =================================================
            # GEMINI QUOTA DETECTION
            # =================================================

            if provider_name == "Gemini":

                retry_seconds = extract_retry_seconds(
                    error_text
                )

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
    # EVERYTHING FAILED
    # =====================================================

    print("----------------------------------------")
    print("❌ ALL AI PROVIDERS FAILED")
    print("----------------------------------------")

    return {
        "answer": None,
        "provider": None,
        "errors": errors
    }
