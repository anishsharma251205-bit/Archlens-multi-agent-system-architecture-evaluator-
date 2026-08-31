import json
from core.models import AgentResult


def validate_output(raw: dict, user_input: str) -> tuple[bool, str]:
    """
    Validate agent output against guardrail rules.
    Returns (is_valid, reason)
    """
    # Rule 1: Score must be within 0-10
    score = raw.get("score", -1)
    if not (0 <= score <= 10):
        return False, f"Score {score} out of range 0-10"

    # Rule 2: Must have at least 1 issue or 1 recommendation
    issues = raw.get("issues", [])
    recs = raw.get("recommendations", [])
    if len(issues) == 0 and len(recs) == 0:
        return False, "No issues or recommendations found"

    # Rule 3: Summary must exist and be non-empty
    summary = raw.get("summary", "").strip()
    if len(summary) < 20:
        return False, "Summary too short or missing"

    # Rule 4: Each issue must have title, description, severity
    for issue in issues:
        if not all(k in issue for k in ["title", "description", "severity"]):
            return False, f"Issue missing required fields: {issue}"
        if issue["severity"] not in ["low", "medium", "high", "critical"]:
            return False, f"Invalid severity: {issue['severity']}"

    return True, "valid"


def run_with_guardrail(fn, system_prompt: str, user_input: str,
                       dimension: str, max_retries: int = 2) -> dict:
    """
    Run an agent function with guardrail validation.
    Retries up to max_retries times if output is invalid.
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            raw = fn(system_prompt, user_input)
            raw["dimension"] = dimension

            is_valid, reason = validate_output(raw, user_input)

            if is_valid:
                return raw
            else:
                print(f"Guardrail failed (attempt {attempt+1}): {reason}")
                last_error = reason

                # Add retry instruction to prompt
                system_prompt += f"\n\nPREVIOUS ATTEMPT FAILED: {reason}. Fix this."

        except json.JSONDecodeError as e:
            print(f"JSON parse failed (attempt {attempt+1}): {e}")
            last_error = str(e)
            system_prompt += "\n\nIMPORTANT: Return ONLY valid JSON, no other text."

        except Exception as e:
            print(f"Agent error (attempt {attempt+1}): {e}")
            last_error = str(e)

    # If all retries failed, return a safe default
    print(f"All {max_retries+1} attempts failed. Using safe default.")
    return {
        "dimension": dimension,
        "score": 5.0,
        "issues": [{"title": "Evaluation failed",
                    "description": f"Could not evaluate: {last_error}",
                    "severity": "medium"}],
        "recommendations": ["Re-run evaluation with more detailed input"],
        "summary": f"Evaluation failed after {max_retries+1} attempts."
    }