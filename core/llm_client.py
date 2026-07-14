import os
import json
import base64
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"


def call_agent(system_prompt: str, user_input: str, expect_json: bool = True):
    """
    Call the LLM with a system prompt and user input.
    If expect_json=True, parses and returns a dict.
    If expect_json=False, returns raw text (for the report agent).
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        temperature=0.3,
    )
    raw = response.choices[0].message.content.strip()

    if not expect_json:
        return raw

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)


def describe_diagram(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """
    Takes an uploaded architecture diagram image and returns a detailed
    text description that can be fed into the existing evaluation agents.
    """
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "You are a software architect. Look at this system "
                                "architecture diagram and write a detailed technical "
                                "description of it: list all components, their connections, "
                                "data flow, deployment details, and any technology labels "
                                "visible. Be thorough and specific — this description will "
                                "be used for architecture evaluation."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{b64_image}"}
                    }
                ]
            }
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()