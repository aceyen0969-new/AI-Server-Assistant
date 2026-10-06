import json

from ai.providers import (
    ask_groq_json,
    ask_gemini_json,
    ask_claude_json,
    ask_openrouter_json,
)


async def ask_with_fallback(
    prompt: str,
):
    """
    Try each AI provider until one returns
    valid JSON.

    Returns:
        tuple[str | None, str | None]

        (
            provider_name,
            raw_response
        )
    """

    providers = [
        (
            "Groq",
            ask_groq_json,
        ),
        (
            "Gemini",
            ask_gemini_json,
        ),
        (
            "Claude",
            ask_claude_json,
        ),
        (
            "OpenRouter",
            ask_openrouter_json,
        ),
    ]

    for provider_name, provider_function in providers:

        print(
            f"AI PROVIDER: Trying {provider_name}..."
        )

        try:

            result = await provider_function(
                prompt
            )

            if not result:
                print(
                    f"AI PROVIDER: "
                    f"{provider_name} returned empty response."
                )
                continue

            try:

                json.loads(result)

            except (
                json.JSONDecodeError,
                TypeError,
            ):

                print(
                    f"AI PROVIDER: "
                    f"{provider_name} returned invalid JSON."
                )

                print(
                    "RAW RESPONSE:"
                )

                print(
                    result
                )

                continue

            print(
                f"AI PROVIDER: "
                f"{provider_name} succeeded."
            )

            return (
                provider_name,
                result,
            )

        except Exception as e:

            print(
                f"AI PROVIDER: "
                f"{provider_name} failed."
            )

            print(
                repr(e)
            )

    print(
        "AI PROVIDER: "
        "All providers failed."
    )

    return (
        None,
        None,
    )