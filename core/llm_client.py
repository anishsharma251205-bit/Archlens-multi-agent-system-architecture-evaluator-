import os
import json
import base64
import time

from dotenv import load_dotenv

load_dotenv()


# LOCAL MODEL

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")


# OPENROUTER CONFIGURATION

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_VISION_MODEL = os.getenv(
    "OPENROUTER_VISION_MODEL",
    "google/gemma-4-26b-a4b-it:free",
)

OPENROUTER_VISION_FALLBACK_MODELS = [
    model.strip()
    for model in os.getenv(
        "OPENROUTER_VISION_FALLBACK_MODELS",
        "google/gemma-4-31b:free;"
        "nvidia/nemotron-3-nano-omni:free",
    ).split(";")
    if model.strip()
]

OPENROUTER_VISION_MODELS = []

for model in [
    OPENROUTER_VISION_MODEL,
    *OPENROUTER_VISION_FALLBACK_MODELS,
]:
    if model and model not in OPENROUTER_VISION_MODELS:
        OPENROUTER_VISION_MODELS.append(model)

OPENROUTER_VISION_TIMEOUT = float(
    os.getenv("OPENROUTER_VISION_TIMEOUT", "60")
)

OPENROUTER_VISION_RETRIES = int(
    os.getenv("OPENROUTER_VISION_RETRIES", "1")
)

OPENROUTER_VISION_RETRY_DELAY = float(
    os.getenv("OPENROUTER_VISION_RETRY_DELAY", "2")
)


# GENERIC LOCAL AGENT

def call_agent(
    system_prompt: str,
    user_input: str,
    expect_json: bool = True,
):
    """
    Call Ollama Mistral for local agent evaluation.

    If expect_json=True, parses and returns a dict.
    If expect_json=False, returns raw text.
    """

    import ollama

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_input,
            },
        ],
        options={
            "temperature": 0.3,
        },
    )

    raw = response["message"]["content"].strip()

    if not expect_json:
        return raw

    if raw.startswith("```"):
        parts = raw.split("```")

        if len(parts) >= 2:
            raw = parts[1].strip()

            if raw.lower().startswith("json"):
                raw = raw[4:].strip()

    return json.loads(raw)


# PUBLIC DIAGRAM DESCRIPTION FUNCTION

def describe_diagram(
    image_bytes: bytes,
    mime_type: str = "image/png",
) -> str:
    """
    Describe an architecture diagram using a vision model.

    Local:
        Ollama + LLaVA

    Cloud:
        OpenRouter vision model pool

    Set ARCHLENS_ENV=cloud in Streamlit Cloud secrets.
    """

    environment = os.getenv(
        "ARCHLENS_ENV",
        "local",
    ).lower()

    if environment == "cloud":
        return _describe_diagram_openrouter(
            image_bytes,
            mime_type,
        )

    return _describe_diagram_ollama(image_bytes)


# LOCAL VISION - OLLAMA + LLAVA

def _describe_diagram_ollama(
    image_bytes: bytes,
) -> str:
    """
    Local diagram analysis using Ollama + LLaVA.
    """

    import ollama

    b64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    response = ollama.chat(
        model="llava",
        messages=[
            {
                "role": "user",
                "content": (
                    "You are a software architect analyzing "
                    "a software architecture diagram. "

                    "Describe ONLY what is visible in the diagram. "

                    "Identify: "
                    "- All visible components "
                    "- Services and applications "
                    "- Databases and storage "
                    "- APIs and protocols "
                    "- Connections between components "
                    "- Direction of data flow "
                    "- Deployment infrastructure "
                    "- Technology labels "
                    "- External systems "
                    "- Queues, caches and messaging systems. "

                    "Do not invent components that are not visible. "
                    "If a label or connection is unclear, explicitly "
                    "state that it is unclear. "

                    "Produce a detailed architecture description that "
                    "will be passed to an architecture evaluation system."
                ),
                "images": [b64],
            }
        ],
    )

    content = response["message"]["content"]

    if not content:
        raise RuntimeError(
            "Ollama LLaVA returned an empty response."
        )

    return content.strip()


# OPENROUTER VISION - SINGLE MODEL

def _call_openrouter_vision_model(
    model: str,
    image_bytes: bytes,
    mime_type: str,
) -> str:
    """
    Call one OpenRouter vision model.
    """

    from openai import OpenAI

    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )

    b64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        timeout=OPENROUTER_VISION_TIMEOUT,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert software architect "
                    "analyzing a software architecture diagram. "

                    "Carefully inspect the image and produce a "
                    "detailed text representation of the architecture. "

                    "Identify: "
                    "- Every visible component "
                    "- Services and applications "
                    "- Databases and storage systems "
                    "- APIs and protocols "
                    "- Connections between components "
                    "- Direction of data flow "
                    "- Deployment infrastructure "
                    "- Technology labels "
                    "- External systems "
                    "- Queues and messaging systems "
                    "- Caches "
                    "- Load balancers and gateways "
                    "- Cloud infrastructure. "

                    "Do NOT invent technologies or components that "
                    "are not visible. "

                    "If a label is difficult to read, say that it "
                    "is unclear rather than guessing. "

                    "If the direction of a connection is unclear, "
                    "state that explicitly. "

                    "The resulting description will be passed to "
                    "an architecture evaluation system."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Analyze this software architecture "
                            "diagram in detail."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:{mime_type};base64,{b64}"
                            ),
                        },
                    },
                ],
            },
        ],
        temperature=0.2,
    )

    if not response.choices:
        raise RuntimeError(
            "OpenRouter returned no choices."
        )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "OpenRouter vision model returned "
            "an empty response."
        )

    return content.strip()


# OPENROUTER VISION - MODEL POOL

def _describe_diagram_openrouter(
    image_bytes: bytes,
    mime_type: str,
) -> str:
    """
    Cloud diagram analysis using an ordered OpenRouter
    vision-model pool.

    Primary:
        OPENROUTER_VISION_MODEL

    Fallbacks:
        OPENROUTER_VISION_FALLBACK_MODELS
    """

    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )

    errors = []

    print("[ArchLens] Vision model pool:")

    for index, model in enumerate(
        OPENROUTER_VISION_MODELS,
        start=1,
    ):
        print(
            f"[ArchLens] Vision model {index}: {model}"
        )

    # Try each vision model

    for model in OPENROUTER_VISION_MODELS:

        for attempt in range(
            1,
            OPENROUTER_VISION_RETRIES + 1,
        ):

            try:

                print(
                    f"[ArchLens] Trying vision model: "
                    f"{model}"
                )

                description = (
                    _call_openrouter_vision_model(
                        model=model,
                        image_bytes=image_bytes,
                        mime_type=mime_type,
                    )
                )

                print(
                    f"[ArchLens] Vision model succeeded: "
                    f"{model}"
                )

                return description

            except Exception as e:

                error_message = (
                    f"{type(e).__name__}: {e}"
                )

                errors.append(
                    f"{model} "
                    f"(attempt {attempt}) -> "
                    f"{error_message}"
                )

                print(
                    f"[ArchLens] Vision model failed: "
                    f"{model}"
                )

                print(
                    f"[ArchLens] Attempt "
                    f"{attempt}/"
                    f"{OPENROUTER_VISION_RETRIES}"
                )

                print(
                    f"[ArchLens] Reason: "
                    f"{error_message}"
                )

                if attempt < OPENROUTER_VISION_RETRIES:

                    time.sleep(
                        OPENROUTER_VISION_RETRY_DELAY
                        * attempt
                    )

        print(
            "[ArchLens] Moving to next vision model."
        )

    # Everything failed

    raise RuntimeError(
        "All configured OpenRouter vision models failed. "
        + " | ".join(errors)
    )