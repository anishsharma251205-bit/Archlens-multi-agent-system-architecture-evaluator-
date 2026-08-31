import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = "mistral"


def classify_complexity(user_input: str) -> str:
    """
    Classify input complexity based on heuristics.
    Returns: 'simple', 'medium', or 'complex'
    """
    word_count = len(user_input.split())
    tech_keywords = [
        "microservices", "kubernetes", "kafka", "redis", "elasticsearch",
        "cassandra", "graphql", "grpc", "istio", "terraform", "serverless",
        "lambda", "ecs", "eks", "cdn", "load balancer", "sharding",
        "replication", "circuit breaker", "service mesh", "event driven",
        "cqrs", "saga", "distributed", "multi-region", "multi-tenant"
    ]
    keyword_count = sum(1 for kw in tech_keywords
                        if kw.lower() in user_input.lower())

    if word_count < 50 and keyword_count < 2:
        return "simple"
    elif word_count < 150 and keyword_count < 5:
        return "medium"
    else:
        return "complex"


def call_ollama(system_prompt: str, user_input: str,
                expect_json: bool = True):
    """Call local Ollama Mistral model."""
    import ollama

    full_prompt = f"{system_prompt}\n\nInput:\n{user_input}"
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": full_prompt}],
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


def route(system_prompt: str, user_input: str,
          expect_json: bool = True, mlops_tracker=None):
    """
    Route to Ollama Mistral.
    Returns (result, model_used, complexity)
    """
    complexity = classify_complexity(user_input)
    start = time.time()

    result = call_ollama(system_prompt, user_input, expect_json)
    latency = time.time() - start

    if mlops_tracker:
        mlops_tracker.log(
            model=OLLAMA_MODEL,
            complexity=complexity,
            latency=latency,
            success=True
        )

    return result, OLLAMA_MODEL, complexity


if __name__ == "__main__":
    simple = "A React frontend with a Node.js backend and PostgreSQL."
    complex_ = "Microservices with Kafka event streaming, Redis caching, \
Kubernetes orchestration, Elasticsearch, and multi-region AWS deployment."

    print(f"Simple input: {classify_complexity(simple)}")
    print(f"Complex input: {classify_complexity(complex_)}")