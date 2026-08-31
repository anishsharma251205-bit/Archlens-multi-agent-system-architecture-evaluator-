import time
from core.router import route, classify_complexity
from core.retriever import retrieve
from core.guardrail import run_with_guardrail
from core.models import AgentResult, EvaluationResult
from core.scoring import compute_final_score
from core.mlops import MLOpsTracker
from core.prompts import (
    STRUCTURE_PROMPT, SECURITY_PROMPT, SCALABILITY_PROMPT,
    PERFORMANCE_PROMPT, COST_PROMPT, REPORT_PROMPT
)


def run_agent(system_prompt: str, dimension: str,
              user_input: str, tracker: MLOpsTracker) -> AgentResult:
    """Run a single evaluation agent with RAG + guardrail + MLOps tracking."""

    # RAG — retrieve relevant best practices
    rag_context = retrieve(user_input, dimension=dimension, top_k=3)

    # Inject RAG context into prompt
    enriched_prompt = system_prompt + "\n\n" + rag_context

    start = time.time()
    success = True
    json_valid = True

    try:
        def call_fn(prompt, inp):
            result, model, complexity = route(prompt, inp, expect_json=True,
                                              mlops_tracker=tracker)
            return result

        raw = run_with_guardrail(
            fn=call_fn,
            system_prompt=enriched_prompt,
            user_input=user_input,
            dimension=dimension
        )

        # Hallucination check
        tracker.check_hallucination(raw, user_input)

        raw["dimension"] = dimension
        agent_result = AgentResult(**raw)

    except Exception as e:
        print(f"Agent {dimension} failed: {e}")
        success = False
        json_valid = False
        agent_result = AgentResult(
            dimension=dimension,
            score=5.0,
            issues=[],
            recommendations=[],
            summary=f"Evaluation error: {str(e)}"
        )

    latency = time.time() - start
    tracker.log_agent(
        dimension=dimension,
        model=tracker.model_used,
        latency=latency,
        success=success,
        json_valid=json_valid,
        score=agent_result.score
    )

    return agent_result


def generate_report(result: EvaluationResult,
                    user_input: str, tracker: MLOpsTracker) -> str:
    """Generate final evaluation report."""
    summary = f"""
System description: {user_input[:500]}

Structure score:    {result.structure.score}/10 — {result.structure.summary}
Security score:     {result.security.score}/10 — {result.security.summary}
Scalability score:  {result.scalability.score}/10 — {result.scalability.summary}
Performance score:  {result.performance.score}/10 — {result.performance.summary}
Cost score:         {result.cost.score}/10 — {result.cost.summary}

Final weighted score: {result.final_score}/10
"""
    try:
        report, model, _ = route(REPORT_PROMPT, summary,
                                 expect_json=False, mlops_tracker=tracker)
        return report
    except Exception as e:
        return f"Report generation failed: {e}"


def evaluate(user_input: str) -> EvaluationResult:
    """
    Main entry point — runs full evaluation pipeline:
    RAG retrieval → agents → guardrail → scoring → MLOps tracking
    """
    complexity = classify_complexity(user_input)
    tracker = MLOpsTracker(user_input=user_input, complexity=complexity)

    print(f"\nComplexity: {complexity}")

    agents = [
        (STRUCTURE_PROMPT,   "structure"),
        (SECURITY_PROMPT,    "security"),
        (SCALABILITY_PROMPT, "scalability"),
        (PERFORMANCE_PROMPT, "performance"),
        (COST_PROMPT,        "cost"),
    ]

    results = {}
    for prompt, dimension in agents:
        print(f"Running {dimension} agent...")
        results[dimension] = run_agent(prompt, dimension,
                                       user_input, tracker)

    evaluation = EvaluationResult(**results)
    evaluation.final_score = compute_final_score(evaluation)

    print("Generating report...")
    evaluation.final_report = generate_report(evaluation, user_input, tracker)

    # Save MLOps data
    tracker.save(result=evaluation)
    print(f"MLOps saved — evaluation id: {tracker.evaluation_id}")

    return evaluation