import os
import json
import base64
from dotenv import load_dotenv

load_dotenv()


def call_agent(system_prompt: str, user_input: str, expect_json: bool = True):
    """
    Call Ollama Mistral for agent evaluation.
    If expect_json=True, parses and returns a dict.
    If expect_json=False, returns raw text (for the report agent).
    """
    import ollama

    response = ollama.chat(
        model="mistral",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        options={"temperature": 0.3}
    )
    raw = response["message"]["content"].strip()

    if not expect_json:
        return raw

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)


def describe_diagram(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """
    Takes an uploaded architecture diagram and returns a detailed
    text description using local Ollama LLaVA vision model.
    """
    import ollama

    b64 = base64.b64encode(image_bytes).decode("utf-8")

    response = ollama.chat(
        model="llava",
        messages=[{
            "role": "user",
            "content": "You are a software architect. Describe this architecture "
                       "diagram in detail: list all components, connections, data "
                       "flow, deployment details, and technology labels visible. "
                       "Be thorough and specific — this will be used for architecture evaluation.",
            "images": [b64]
        }]
    )
    return response["message"]["content"].strip()