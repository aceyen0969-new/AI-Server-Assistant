import os
import asyncio

from dotenv import load_dotenv
from google import genai
from openai import OpenAI
from groq import Groq
from anthropic import Anthropic


load_dotenv()


# =========================================================
# API KEYS
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


# =========================================================
# CLIENTS
# =========================================================

gemini_client = None
openrouter_client = None
groq_client = None
anthropic_client = None


if GEMINI_API_KEY:
    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )


if OPENROUTER_API_KEY:
    openrouter_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY
    )


if GROQ_API_KEY:
    groq_client = Groq(
        api_key=GROQ_API_KEY
    )


if ANTHROPIC_API_KEY:
    anthropic_client = Anthropic(
        api_key=ANTHROPIC_API_KEY
    )


# =========================================================
# MODELS
# =========================================================

GEMINI_MODEL = "gemini-3.8-flash"

CLAUDE_MODEL = "claude-sonnet-4-5"

OPENROUTER_MODEL = "openrouter/free"

GROQ_MODEL = "openai/gpt-oss-120b"


# =========================================================
# GEMINI NORMAL CHAT
# =========================================================

async def ask_gemini(prompt):

    if gemini_client is None:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    response = await asyncio.to_thread(
        gemini_client.models.generate_content,
        model=GEMINI_MODEL,
        contents=prompt
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return response.text


# =========================================================
# GEMINI JSON
# =========================================================

async def ask_gemini_json(prompt):

    if gemini_client is None:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    response = await asyncio.to_thread(
        gemini_client.models.generate_content,
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty JSON response."
        )

    return response.text


# =========================================================
# CLAUDE NORMAL CHAT
# =========================================================

async def ask_claude(prompt):

    if anthropic_client is None:
        raise RuntimeError(
            "Anthropic API key is not configured."
        )

    response = await asyncio.to_thread(
        anthropic_client.messages.create,
        model=CLAUDE_MODEL,
        max_tokens=2048,
        system=(
            "You are the AI Server Assistant inside a Discord server.\n\n"
            "Answer the user's request directly and naturally.\n"
            "Use the server information supplied in the prompt.\n"
            "Do not claim to have performed Discord actions.\n"
            "Do not output internal analysis or safety classifications.\n"
            "Do not greet the user unless they greeted you.\n"
            "Keep responses reasonably concise.\n"
            "Use Markdown when useful."
        ),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    if not response.content:
        raise RuntimeError(
            "Claude returned an empty response."
        )

    text_parts = []

    for block in response.content:

        if hasattr(block, "text"):

            text_parts.append(
                block.text
            )

    answer = "\n".join(
        text_parts
    ).strip()

    if not answer:
        raise RuntimeError(
            "Claude returned an empty response."
        )

    return answer


# =========================================================
# CLAUDE JSON
# =========================================================

async def ask_claude_json(prompt):

    if anthropic_client is None:
        raise RuntimeError(
            "Anthropic API key is not configured."
        )

    response = await asyncio.to_thread(
        anthropic_client.messages.create,
        model=CLAUDE_MODEL,
        max_tokens=2048,
        system=(
            "You are a Discord server organization planner.\n\n"
            "Return ONLY valid JSON.\n"
            "Do not return Markdown.\n"
            "Do not return code fences.\n"
            "Do not return explanations.\n"
            "Follow the exact JSON structure requested."
        ),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    if not response.content:
        raise RuntimeError(
            "Claude returned an empty JSON response."
        )

    text_parts = []

    for block in response.content:

        if hasattr(block, "text"):

            text_parts.append(
                block.text
            )

    answer = "\n".join(
        text_parts
    ).strip()

    if not answer:
        raise RuntimeError(
            "Claude returned an empty JSON response."
        )

    return answer


# =========================================================
# OPENROUTER NORMAL CHAT
# =========================================================

async def ask_openrouter(prompt):

    if openrouter_client is None:
        raise RuntimeError(
            "OpenRouter API key is not configured."
        )

    response = await asyncio.to_thread(
        openrouter_client.chat.completions.create,
        model=OPENROUTER_MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are the AI Server Assistant inside a Discord server.

Your job is to directly answer the user's question using
the server information provided in the prompt.

IMPORTANT BEHAVIOR:

- Answer the user's actual question.
- Do NOT greet the user unless they greeted you.
- Do NOT introduce yourself.
- Do NOT give a generic list of possible services.
- Do NOT repeat the user's question.
- Do NOT pretend to have performed Discord actions.
- Do NOT output internal safety classifications.
- Do NOT output analysis or reasoning.
- Do NOT output JSON unless specifically requested.
- Use the actual server information supplied in the prompt.
- If the question is about server statistics, use the supplied statistics.
- If the question is about channels, use the supplied channel structure.
- If the question is asking for advice, give practical advice.
- Keep the response reasonably concise.
- Use Markdown when useful.
- Do not use Discord asset URLs.
- Do not create fake Discord emoji links.

Respond directly to the user's request.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = (
        response.choices[0]
        .message
        .content
    )

    if not answer:
        raise RuntimeError(
            "OpenRouter returned an empty response."
        )

    return answer


# =========================================================
# OPENROUTER JSON
# =========================================================

async def ask_openrouter_json(prompt):

    if openrouter_client is None:
        raise RuntimeError(
            "OpenRouter API key is not configured."
        )

    response = await asyncio.to_thread(
        openrouter_client.chat.completions.create,
        model=OPENROUTER_MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are a Discord server organization planner.

You MUST return a valid JSON object.

Return ONLY JSON.

Do not return:
- Markdown
- Code fences
- Explanations outside JSON
- Greetings
- Safety classifications
- Analysis

Follow the exact JSON structure requested by the user.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={
            "type": "json_object"
        }
    )

    answer = (
        response.choices[0]
        .message
        .content
    )

    if not answer:
        raise RuntimeError(
            "OpenRouter returned an empty JSON response."
        )

    return answer


# =========================================================
# GROQ NORMAL CHAT
# =========================================================

async def ask_groq(prompt):

    if groq_client is None:
        raise RuntimeError(
            "Groq API key is not configured."
        )

    response = await asyncio.to_thread(
        groq_client.chat.completions.create,
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful Discord server assistant. "
                    "Answer the user's request directly and naturally. "
                    "Do not output safety classifications, "
                    "moderation labels, or internal analysis."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = (
        response.choices[0]
        .message
        .content
    )

    if not answer:
        raise RuntimeError(
            "Groq returned an empty response."
        )

    return answer


# =========================================================
# GROQ JSON
# =========================================================

async def ask_groq_json(prompt):

    if groq_client is None:
        raise RuntimeError(
            "Groq API key is not configured."
        )

    response = await asyncio.to_thread(
        groq_client.chat.completions.create,
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are a Discord server organization planner.

You MUST return a valid JSON object.

Return ONLY JSON.

Do not return:
- Markdown
- Code fences
- Explanations outside JSON
- Greetings
- Safety classifications
- Analysis

Follow the exact JSON structure requested by the user.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={
            "type": "json_object"
        }
    )

    answer = (
        response.choices[0]
        .message
        .content
    )

    if not answer:
        raise RuntimeError(
            "Groq returned an empty JSON response."
        )

    return answer