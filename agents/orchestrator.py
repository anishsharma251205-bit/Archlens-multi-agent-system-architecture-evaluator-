from core.llm_client import call_agent
from core.models import AgentResult, EvaluationResult
from core.scoring import compute_final_score
from core.prompts import (
    STRUCTURE_PROMPT, SECURITY_PROMPT, SCALABILITY_PROMPT,
    PERFORMANCE_PROMPT, COST_PROMPT, REPORT_PROMPT
)


def run_agent(system_prompt: str, dimension: str, user_input: str) -> AgentResult:
    raw = call_agent(system_prompt, user_input)
    raw["dimension"] = dimension
    return AgentResult(**raw)


def _format_all_issues(result: EvaluationResult) -> str:
    lines = []
    for dim_result in [result.structure, result.security, result.scalability,
                        result.performance, result.cost]:
        for issue in dim_result.issues:
            lines.append(f"[{dim_result.dimension.upper()}] [{issue.severity.upper()}] "
                         f"{issue.title}: {issue.description}")
    return "\n".join(lines)


def generate_report(result: EvaluationResult, user_input: str) -> str:
    summary = f"""
System description: {user_input[:500]}

Structure score: {result.structure.score}/10 — {result.structure.summary}
Security score: {result.security.score}/10 — {result.security.summary}
Scalability score: {result.scalability.score}/10 — {result.scalability.summary}
Performance score: {result.performance.score}/10 — {result.performance.summary}
Cost score: {result.cost.score}/10 — {result.cost.summary}

Final weighted score: {result.final_score}/10

All issues found:
{_format_all_issues(result)}
"""
    response = call_agent(REPORT_PROMPT, summary, expect_json=False)
    return response if isinstance(response, str) else str(response)


def evaluate(user_input: str) -> EvaluationResult:
    """Main entry point — runs all agents and returns a complete EvaluationResult."""
    agents = [
        (STRUCTURE_PROMPT, "structure"),
        (SECURITY_PROMPT, "security"),
        (SCALABILITY_PROMPT, "scalability"),
        (PERFORMANCE_PROMPT, "performance"),
        (COST_PROMPT, "cost"),
    ]

    results = {}
    for prompt, dimension in agents:
        print(f"Running {dimension} agent...")
        results[dimension] = run_agent(prompt, dimension, user_input)

    evaluation = EvaluationResult(**results)
    evaluation.final_score = compute_final_score(evaluation)

    print("Generating final report...")
    evaluation.final_report = generate_report(evaluation, user_input)

    return evaluation