
from typing import Any


# ============================================================
# VALIDATE AGENT OUTPUT
# ============================================================

def validate_output(
    raw: Any,
    user_input: str
) -> tuple[bool, str]:
    """
    Validate agent output against ArchLens guardrail rules.

    Returns:
        (is_valid, reason)
    """

    # ========================================================
    # RULE 0 — OUTPUT MUST BE A DICTIONARY
    # ========================================================

    if not isinstance(raw, dict):
        return False, (
            f"Expected a JSON object, "
            f"got {type(raw).__name__}"
        )

    # ========================================================
    # RULE 1 — SCORE MUST BE NUMERIC AND 0-10
    # ========================================================

    score = raw.get("score")

    if isinstance(score, bool):
        return False, "Score must be a number, not boolean"

    if not isinstance(score, (int, float)):
        return False, (
            f"Score must be numeric, "
            f"got {score!r}"
        )

    if not 0 <= score <= 10:
        return False, (
            f"Score {score} out of range 0-10"
        )

    # ========================================================
    # RULE 2 — ISSUES MUST BE A LIST
    # ========================================================

    issues = raw.get("issues")

    if not isinstance(issues, list):
        return False, (
            "'issues' must be a JSON array"
        )

    # ========================================================
    # RULE 3 — RECOMMENDATIONS MUST BE A LIST
    # ========================================================

    recommendations = raw.get("recommendations")

    if not isinstance(recommendations, list):
        return False, (
            "'recommendations' must be a JSON array"
        )

    # ========================================================
    # RULE 4 — AT LEAST ONE ISSUE OR RECOMMENDATION
    # ========================================================

    if len(issues) == 0 and len(recommendations) == 0:
        return False, (
            "No issues or recommendations found"
        )

    # ========================================================
    # RULE 5 — SUMMARY MUST EXIST
    # ========================================================

    summary = raw.get("summary")

    if not isinstance(summary, str):
        return False, (
            "'summary' must be a string"
        )

    summary = summary.strip()

    if len(summary) < 20:
        return False, (
            "Summary too short or missing "
            "(minimum 20 characters)"
        )

    # ========================================================
    # RULE 6 — VALIDATE ISSUES
    # ========================================================

    valid_severities = {
        "low",
        "medium",
        "high",
        "critical"
    }

    for index, issue in enumerate(issues):

        if not isinstance(issue, dict):
            return False, (
                f"Issue #{index + 1} must be a JSON object"
            )

        required_fields = [
            "title",
            "description",
            "severity"
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in issue
        ]

        if missing_fields:
            return False, (
                f"Issue #{index + 1} missing fields: "
                f"{missing_fields}"
            )

        if not isinstance(issue["title"], str):
            return False, (
                f"Issue #{index + 1} title must be a string"
            )

        if not isinstance(issue["description"], str):
            return False, (
                f"Issue #{index + 1} description must be a string"
            )

        severity = issue["severity"]

        if severity not in valid_severities:
            return False, (
                f"Issue #{index + 1} has invalid "
                f"severity: {severity!r}"
            )

    # ========================================================
    # RULE 7 — VALIDATE RECOMMENDATIONS
    # ========================================================

    for index, recommendation in enumerate(
        recommendations
    ):

        if not isinstance(recommendation, str):
            return False, (
                f"Recommendation #{index + 1} "
                f"must be a string"
            )

        if not recommendation.strip():
            return False, (
                f"Recommendation #{index + 1} "
                f"is empty"
            )

    # ========================================================
    # VALID
    # ========================================================

    return True, "valid"


# ============================================================
# RUN AGENT WITH GUARDRAIL + RETRIES
# ============================================================

def run_with_guardrail(
    fn,
    system_prompt: str,
    user_input: str,
    dimension: str,
    max_retries: int = 2
) -> dict:
    """
    Execute an agent with validation and retry protection.

    Flow:

        LLM
         ↓
        Parse JSON
         ↓
        Validate schema
         ↓
        Validate content
         ↓
        Retry if invalid
         ↓
        Safe fallback
    """

    last_error = None

    for attempt in range(max_retries + 1):

        try:

            # =================================================
            # CALL MODEL
            # =================================================

            raw = fn(
                system_prompt,
                user_input
            )

            # =================================================
            # VALIDATE OUTPUT
            # =================================================

            is_valid, reason = validate_output(
                raw,
                user_input
            )

            if is_valid:

                # Add dimension only after validation.
                raw["dimension"] = dimension

                return raw

            # =================================================
            # GUARDRAIL FAILURE
            # =================================================

            print(
                f"Guardrail failed "
                f"(attempt {attempt + 1}/"
                f"{max_retries + 1}): "
                f"{reason}"
            )

            last_error = reason

            # Make the retry instruction stronger
            system_prompt += f"""

PREVIOUS RESPONSE FAILED ARCHLENS GUARDRAILS.

Failure:
{reason}

You MUST correct this in your next response.

STRICT OUTPUT REQUIREMENTS:
- Return exactly ONE JSON object.
- Do NOT return multiple JSON objects.
- Do NOT return a JSON array.
- Do NOT include markdown.
- Do NOT include explanations outside JSON.
- "score" MUST be a number from 0 to 10.
- "issues" MUST be an array.
- "recommendations" MUST be an array.
- "summary" MUST be a string of at least 20 characters.
- Every issue MUST contain:
  title, description, severity.
- severity MUST be one of:
  low, medium, high, critical.

Return ONLY the corrected JSON object.
"""

        except ValueError as e:
            """
            router.py currently converts JSON parsing errors
            into ValueError.

            Therefore this catches errors such as:

                Invalid JSON returned by model:
                Extra data...

            """

            print(
                f"Output parsing failed "
                f"(attempt {attempt + 1}/"
                f"{max_retries + 1}): {e}"
            )

            last_error = str(e)

            system_prompt += """

PREVIOUS RESPONSE CONTAINED INVALID JSON.

STRICT REQUIREMENTS:
- Return exactly ONE JSON object.
- No multiple JSON objects.
- No JSON array.
- No markdown fences.
- No text before or after the JSON.
- "score" must be a numeric value from 0 to 10.

Return ONLY valid JSON.
"""

        except Exception as e:

            print(
                f"Agent error "
                f"(attempt {attempt + 1}/"
                f"{max_retries + 1}): {e}"
            )

            last_error = str(e)

            system_prompt += f"""

PREVIOUS ATTEMPT FAILED:

{last_error}

Retry the evaluation and return ONLY one valid JSON object.
"""

    # ========================================================
    # SAFE FALLBACK
    # ========================================================

    print(
        f"All {max_retries + 1} attempts failed. "
        f"Using safe default."
    )

    return {
        "dimension": dimension,
        "score": 5.0,
        "issues": [
            {
                "title": "Evaluation failed",
                "description": (
                    f"ArchLens could not reliably evaluate "
                    f"this dimension. Error: {last_error}"
                ),
                "severity": "medium"
            }
        ],
        "recommendations": [
            "Re-run the evaluation with more detailed "
            "architecture information."
        ],
        "summary": (
            f"Evaluation failed after "
            f"{max_retries + 1} attempts."
        )
    }

