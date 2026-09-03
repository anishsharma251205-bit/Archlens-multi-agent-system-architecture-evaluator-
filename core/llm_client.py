
import os
import json
import base64

from dotenv import load_dotenv

load_dotenv()


def call_agent(system_prompt: str, user_input: str, expect_json: bool = True):
    """
    Call Ollama Mistral for local agent evaluation.

    If expect_json=True, parses and returns a dict.
    If expect_json=False, returns raw text.
    """
    import ollama

    response = ollama.chat(
        model="mistral",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        options={"temperature": 0.3},
    )

    raw = response["message"]["content"].strip()

    if not expect_json:
        return raw

    if raw.startswith("```"):
        raw = raw.split("```")[1]

        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)


def describe_diagram(
    image_bytes: bytes,
    mime_type: str = "image/png",
) -> str:
    """
    Describe an architecture diagram using a vision model.

    Local:
        Ollama + LLaVA

    Cloud:
        OpenRouter vision model

    Set ARCHLENS_ENV=cloud in Streamlit Cloud secrets.
    """

    environment = os.getenv("ARCHLENS_ENV", "local").lower()

    if environment == "cloud":
        return _describe_diagram_openrouter(image_bytes, mime_type)

    return _describe_diagram_ollama(image_bytes)


def _describe_diagram_ollama(image_bytes: bytes) -> str:
    """
    Local diagram analysis using Ollama + LLaVA.
    """
    import ollama

    b64 = base64.b64encode(image_bytes).decode("utf-8")

    response = ollama.chat(
        model="llava",
        messages=[
            {
                "role": "user",
                "content": (
                    "You are a software architect. Describe this architecture "
                    "diagram in detail: list all components, connections, data "
                    "flow, deployment details, and technology labels visible. "
                    "Be thorough and specific — this will be used for architecture "
                    "evaluation."
                ),
                "images": [b64],
            }
        ],
    )

    return response["message"]["content"].strip()


def _describe_diagram_openrouter(
    image_bytes: bytes,
    mime_type: str,
) -> str:
    """
    Cloud diagram analysis using an OpenRouter vision-capable model.
    """

    from openai import OpenAI

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )

    model = os.getenv(
        "OPENROUTER_VISION_MODEL",
        "google/gemini-2.5-flash"
    )

    b64 = base64.b64encode(image_bytes).decode("utf-8")

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        timeout=60.0,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a software architect analyzing an architecture "
                    "diagram. Carefully inspect the image and produce a detailed "
                    "text description of the architecture. Identify all visible "
                    "components, services, databases, APIs, connections, data "
                    "flows, deployment details, protocols, and technology labels. "
                    "Do not invent components that are not visible. Clearly "
                    "describe uncertainty when a label or connection is unclear. "
                    "The resulting description will be passed to an architecture "
                    "evaluation system."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Analyze this software architecture diagram in detail."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:{mime_type};base64,{b64}"
                            )
                        },
                    },
                ],
            },
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "OpenRouter vision model returned an empty response."
        )

    return content.strip()

