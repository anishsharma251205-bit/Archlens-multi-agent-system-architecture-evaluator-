import os
import json
import time

import ollama
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Model configuration

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "mistral"
)

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

# Text / agent models

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "nvidia/nemotron-3-super-120b-a12b:free"
)

OPENROUTER_FALLBACK_MODELS = [
    model.strip()
    for model in os.getenv(
        "OPENROUTER_FALLBACK_MODELS",
        "google/gemma-4-26b-a4b-it:free;"
        "z-ai/glm-5.2:free"
    ).split(";")
    if model.strip()
]

OPENROUTER_MODELS = []

for model in [
    OPENROUTER_MODEL,
    *OPENROUTER_FALLBACK_MODELS
]:
    if model and model not in OPENROUTER_MODELS:
        OPENROUTER_MODELS.append(model)

# OpenRouter settings

OPENROUTER_TIMEOUT = float(
    os.getenv(
        "OPENROUTER_TIMEOUT",
        "45"
    )
)

OPENROUTER_RETRIES = int(
    os.getenv(
        "OPENROUTER_RETRIES",
        "2"
    )
)

OPENROUTER_RETRY_DELAY = float(
    os.getenv(
        "OPENROUTER_RETRY_DELAY",
        "2"
    )
)

# OpenRouter client

openrouter_client = None

if OPENROUTER_API_KEY:
    openrouter_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        timeout=OPENROUTER_TIMEOUT,
    )

# Complexity classifier

def classify_complexity(user_input: str) -> str:
    """
    Classify architecture complexity.

    Returns:
        simple
        medium
        complex
    """

    if not user_input:
        return "simple"

    word_count = len(user_input.split())

    tech_keywords = [
        "microservices",
        "kubernetes",
        "kafka",
        "redis",
        "elasticsearch",
        "cassandra",
        "graphql",
        "grpc",
        "istio",
        "terraform",
        "serverless",
        "lambda",
        "ecs",
        "eks",
        "cdn",
        "load balancer",
        "sharding",
        "replication",
        "circuit breaker",
        "service mesh",
        "event driven",
        "cqrs",
        "saga",
        "distributed",
        "multi-region",
        "multi-tenant"
    ]

    input_lower = user_input.lower()

    keyword_count = sum(
        1
        for keyword in tech_keywords
        if keyword.lower() in input_lower
    )

    if word_count < 50 and keyword_count < 2:
        return "simple"

    if word_count < 150 and keyword_count < 5:
        return "medium"

    return "complex"

# JSON cleaning

def parse_json_response(raw: str):
    """
    Safely convert model output into JSON.
    """

    if not raw:
        raise ValueError(
            "Model returned an empty response"
        )

    raw = raw.strip()

    if raw.startswith("```"):
        parts = raw.split("```")

        if len(parts) >= 2:
            raw = parts[1].strip()

            if raw.lower().startswith("json"):
                raw = raw[4:].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    object_start = raw.find("{")
    array_start = raw.find("[")

    starts = [
        x
        for x in (
            object_start,
            array_start
        )
        if x != -1
    ]

    if not starts:
        raise ValueError(
            "No JSON object or array found in model response:\n"
            f"{raw[:1000]}"
        )

    start = min(starts)

    object_end = raw.rfind("}")
    array_end = raw.rfind("]")

    end = max(
        object_end,
        array_end
    )

    if end == -1 or end <= start:
        raise ValueError(
            "Could not extract JSON from model response:\n"
            f"{raw[:1000]}"
        )

    json_text = raw[start:end + 1]

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            "Invalid JSON returned by model:\n"
            f"{e}\n\n"
            f"Response:\n{raw[:1500]}"
        )

# ArchLens output validation

def validate_archlens_output(result):
    """
    Validate the JSON structure expected from ArchLens agents.
    """

    if not isinstance(result, dict):
        raise ValueError(
            f"Expected a JSON object, got "
            f"{type(result).__name__}"
        )

    if "dimension" in result:
        if not isinstance(
            result["dimension"],
            str
        ):
            raise ValueError(
                "'dimension' must be a string"
            )

    if "score" not in result:
        raise ValueError(
            "ArchLens output missing 'score'"
        )

    score = result["score"]

    if isinstance(score, bool):
        raise ValueError(
            "Score must be numeric, not boolean"
        )

    if not isinstance(
        score,
        (int, float)
    ):
        raise ValueError(
            f"Score must be numeric, got {score!r}"
        )

    if not 0 <= score <= 10:
        raise ValueError(
            f"Score must be between 0 and 10, got {score}"
        )

    if "issues" not in result:
        raise ValueError(
            "ArchLens output missing 'issues'"
        )

    if not isinstance(
        result["issues"],
        list
    ):
        raise ValueError(
            "'issues' must be a list"
        )

    if "recommendations" not in result:
        raise ValueError(
            "ArchLens output missing 'recommendations'"
        )

    if not isinstance(
        result["recommendations"],
        list
    ):
        raise ValueError(
            "'recommendations' must be a list"
        )

    if "summary" not in result:
        raise ValueError(
            "ArchLens output missing 'summary'"
        )

    summary = result["summary"]

    if not isinstance(
        summary,
        str
    ):
        raise ValueError(
            "'summary' must be a string"
        )

    if len(summary.strip()) < 20:
        raise ValueError(
            "'summary' is too short"
        )

    if (
        not result["issues"]
        and not result["recommendations"]
    ):
        raise ValueError(
            "ArchLens output contains no issues "
            "and no recommendations"
        )

    for index, issue in enumerate(
        result["issues"]
    ):
        if not isinstance(
            issue,
            dict
        ):
            raise ValueError(
                f"Issue {index} must be an object"
            )

        required_fields = [
            "title",
            "description",
            "severity"
        ]

        for field in required_fields:
            if field not in issue:
                raise ValueError(
                    f"Issue {index} missing '{field}'"
                )

        severity = str(
            issue["severity"]
        ).lower()

        valid_severities = {
            "low",
            "medium",
            "high",
            "critical"
        }

        if severity not in valid_severities:
            raise ValueError(
                f"Issue {index} has invalid "
                f"severity '{issue['severity']}'"
            )

    for index, recommendation in enumerate(
        result["recommendations"]
    ):
        if not isinstance(
            recommendation,
            str
        ):
            raise ValueError(
                f"Recommendation {index} must be a string"
            )

        if not recommendation.strip():
            raise ValueError(
                f"Recommendation {index} is empty"
            )

    return True

# Ollama / Mistral

def call_ollama(
    system_prompt: str,
    user_input: str,
    expect_json: bool = True
):
    """
    Call the local Ollama text model.
    """

    print(
        f"[ArchLens] Using Ollama TEXT model: {OLLAMA_MODEL}"
    )

    full_prompt = f"""
{system_prompt}

ARCHLENS AGENT OUTPUT RULES

You are ONE specialized ArchLens evaluation agent.

Your task is to evaluate ONLY the dimension specified
by your system instructions.

IMPORTANT RULES:

1. Analyze ONLY the requested architecture dimension.
2. DO NOT evaluate other dimensions.
3. Return EXACTLY ONE JSON object.
4. NEVER return multiple JSON objects.
5. NEVER return a JSON array containing multiple evaluation objects.
6. Do NOT provide separate evaluations for other dimensions.
7. Do NOT write explanations before the JSON.
8. Do NOT write explanations after the JSON.
9. Do NOT use Markdown code fences.
10. Do NOT invent technologies that are not present.
11. Base your evaluation only on the provided architecture.
12. Do not assume an unspecified feature is absent.
13. Distinguish PRESENT, ABSENT, and UNSPECIFIED.
14. The entire response must be valid JSON.
15. Stop generating immediately after the closing curly brace.

REQUIRED JSON FORMAT

{{
  "dimension": "requested_dimension",
  "score": 0,
  "issues": [
    {{
      "title": "Short issue title",
      "description": "Detailed explanation of the issue",
      "severity": "medium"
    }}
  ],
  "recommendations": [
    "Practical recommendation"
  ],
  "summary": "Meaningful summary of this dimension"
}}

Architecture/Input:

{user_input}
"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": full_prompt
            }
        ],
        options={
            "temperature": 0.2
        }
    )

    raw = response["message"]["content"].strip()

    if not expect_json:
        return raw

    result = parse_json_response(raw)

    validate_archlens_output(result)

    return result

# OpenRouter single model

def _call_openrouter_model(
    model: str,
    system_prompt: str,
    user_input: str,
    expect_json: bool = True
):
    """
    Call one specific OpenRouter TEXT model.
    """

    full_prompt = f"""
{system_prompt}

IMPORTANT:

- Analyze only the provided architecture.
- Do not invent technologies that are not present.
- Base recommendations on the provided architecture.
- Do not assume components that were not provided.
- Do not treat unspecified features as absent.
- Distinguish PRESENT, ABSENT, and UNSPECIFIED.
- Evaluate ONLY the requested dimension.
- Return exactly ONE JSON object.
- Do not return multiple JSON objects.
- The JSON must contain:
  - dimension
  - score
  - issues
  - recommendations
  - summary
- score must be a number from 0 to 10.
- issues must be a JSON array.
- recommendations must be a JSON array.
- summary must be a meaningful string.
- Do not wrap JSON in Markdown.
- Do not add explanations before or after the JSON.

Your entire response must be ONE valid JSON object.

Architecture/Input:

{user_input}
"""

    print(
        f"[ArchLens] Trying OpenRouter TEXT model: {model}"
    )

    response = openrouter_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": full_prompt
            }
        ],
        temperature=0.2,
        timeout=OPENROUTER_TIMEOUT,
    )

    if not response.choices:
        raise ValueError(
            "OpenRouter returned no choices."
        )

    message = response.choices[0].message

    if not message.content:
        raise ValueError(
            "OpenRouter returned an empty response."
        )

    raw = message.content.strip()

    actual_model = getattr(
        response,
        "model",
        None
    )

    if not actual_model:
        actual_model = model

    print(
        f"[ArchLens] OpenRouter TEXT model used: "
        f"{actual_model}"
    )

    if not expect_json:
        return raw, actual_model

    result = parse_json_response(raw)

    validate_archlens_output(result)

    return result, actual_model

# OpenRouter text model pool

def call_openrouter(
    system_prompt: str,
    user_input: str,
    expect_json: bool = True
):
    """
    Call OpenRouter using the TEXT model pool.

    Returns:
        result,
        actual_model_used
    """

    if not openrouter_client:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )

    if not OPENROUTER_MODELS:
        raise RuntimeError(
            "No OpenRouter TEXT models are configured."
        )

    errors = []

    print(
        f"[ArchLens] TEXT OpenRouter pool: "
        f"{OPENROUTER_MODELS}"
    )

    for model in OPENROUTER_MODELS:

        for attempt in range(
            1,
            OPENROUTER_RETRIES + 1
        ):
            try:

                result, actual_model = (
                    _call_openrouter_model(
                        model=model,
                        system_prompt=system_prompt,
                        user_input=user_input,
                        expect_json=expect_json
                    )
                )

                print(
                    f"[ArchLens] OpenRouter TEXT model accepted: "
                    f"{actual_model}"
                )

                return (
                    result,
                    actual_model
                )

            except Exception as e:

                error_message = (
                    f"{type(e).__name__}: {e}"
                )

                errors.append(
                    f"{model} "
                    f"(attempt {attempt}) "
                    f"-> {error_message}"
                )

                print(
                    f"[ArchLens] OpenRouter TEXT model failed: "
                    f"{model}"
                )

                print(
                    f"[ArchLens] Attempt "
                    f"{attempt}/{OPENROUTER_RETRIES}"
                )

                print(
                    f"[ArchLens] Reason: "
                    f"{error_message}"
                )

                if attempt < OPENROUTER_RETRIES:
                    time.sleep(
                        OPENROUTER_RETRY_DELAY * attempt
                    )

        print(
            "[ArchLens] Moving to next OpenRouter TEXT model."
        )

    raise RuntimeError(
        "All configured OpenRouter TEXT models failed.\n"
        + "\n".join(errors)
    )

# Main text router

def route(
    system_prompt: str,
    user_input: str,
    expect_json: bool = True,
    mlops_tracker=None
):
    """
    Intelligent TEXT model router.

    SIMPLE / MEDIUM:
        Ollama -> OpenRouter TEXT pool

    COMPLEX:
        OpenRouter TEXT pool -> Ollama

    Returns:
        result,
        model_used,
        complexity
    """

    complexity = classify_complexity(
        user_input
    )

    print(
        f"[ArchLens] TEXT routing — complexity: "
        f"{complexity}"
    )

    print(
        f"[ArchLens] TEXT OpenRouter pool: "
        f"{OPENROUTER_MODELS}"
    )

    start = time.time()

    # Simple / medium text input

    if complexity in (
        "simple",
        "medium"
    ):

        print(
            "[ArchLens] Simple/Medium TEXT input "
            "-> Ollama first"
        )

        try:

            result = call_ollama(
                system_prompt,
                user_input,
                expect_json
            )

            latency = time.time() - start

            if mlops_tracker:
                mlops_tracker.log(
                    model=OLLAMA_MODEL,
                    complexity=complexity,
                    latency=latency,
                    success=True
                )

            return (
                result,
                OLLAMA_MODEL,
                complexity
            )

        except Exception as ollama_error:

            print(
                f"[ArchLens] Ollama TEXT failed: "
                f"{ollama_error}"
            )

            if openrouter_client:

                try:

                    print(
                        "[ArchLens] Ollama failed "
                        "-> OpenRouter TEXT fallback"
                    )

                    result, actual_model = (
                        call_openrouter(
                            system_prompt,
                            user_input,
                            expect_json
                        )
                    )

                    model_name = (
                        f"openrouter:{actual_model}"
                    )

                    if mlops_tracker:
                        mlops_tracker.log(
                            model=model_name,
                            complexity=complexity,
                            latency=time.time() - start,
                            success=True
                        )

                    return (
                        result,
                        model_name,
                        complexity
                    )

                except Exception as openrouter_error:

                    print(
                        "[ArchLens] OpenRouter TEXT "
                        f"fallback failed: {openrouter_error}"
                    )

            if mlops_tracker:
                mlops_tracker.log(
                    model=OLLAMA_MODEL,
                    complexity=complexity,
                    latency=time.time() - start,
                    success=False
                )

            raise ollama_error

    # Complex text input

    if complexity == "complex":

        print(
            "[ArchLens] Complex TEXT input "
            "-> OpenRouter TEXT pool"
        )

        openrouter_error = None

        if openrouter_client:

            try:

                result, actual_model = (
                    call_openrouter(
                        system_prompt,
                        user_input,
                        expect_json
                    )
                )

                model_name = (
                    f"openrouter:{actual_model}"
                )

                latency = time.time() - start

                if mlops_tracker:
                    mlops_tracker.log(
                        model=model_name,
                        complexity=complexity,
                        latency=latency,
                        success=True
                    )

                return (
                    result,
                    model_name,
                    complexity
                )

            except Exception as e:

                openrouter_error = e

                print(
                    f"[ArchLens] OpenRouter TEXT pool failed: "
                    f"{e}"
                )

        else:

            openrouter_error = (
                "OpenRouter client unavailable"
            )

        print(
            "[ArchLens] Falling back to Ollama TEXT model"
        )

        try:

            result = call_ollama(
                system_prompt,
                user_input,
                expect_json
            )

            latency = time.time() - start

            if mlops_tracker:
                mlops_tracker.log(
                    model=f"{OLLAMA_MODEL}:fallback",
                    complexity=complexity,
                    latency=latency,
                    success=True
                )

            return (
                result,
                f"{OLLAMA_MODEL}:fallback",
                complexity
            )

        except Exception as ollama_error:

            if mlops_tracker:
                mlops_tracker.log(
                    model=OLLAMA_MODEL,
                    complexity=complexity,
                    latency=time.time() - start,
                    success=False
                )

            raise RuntimeError(
                "Both OpenRouter TEXT and Ollama failed.\n"
                f"OpenRouter error: {openrouter_error}\n"
                f"Ollama error: {ollama_error}"
            )

# Local test

if __name__ == "__main__":

    simple = (
        "A React frontend with a Node.js backend "
        "and PostgreSQL."
    )

    medium = (
        "A React frontend with Node.js backend, "
        "PostgreSQL database, Redis caching and "
        "Docker deployment."
    )

    complex_architecture = (
        "A distributed microservices architecture using "
        "Kafka event streaming, Redis caching, Kubernetes "
        "orchestration, Elasticsearch, PostgreSQL, "
        "service mesh, multi-region deployment and "
        "AWS infrastructure."
    )

    print(
        f"Simple input: "
        f"{classify_complexity(simple)}"
    )

    print(
        f"Medium input: "
        f"{classify_complexity(medium)}"
    )

    print(
        f"Complex input: "
        f"{classify_complexity(complex_architecture)}"
    )

    print(
        "\nConfigured OpenRouter TEXT models:"
    )

    for index, model in enumerate(
        OPENROUTER_MODELS,
        start=1
    ):
        print(
            f"{index}. {model}"
        )