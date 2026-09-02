
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.router import route, classify_complexity
from core.retriever import retrieve
from core.guardrail import run_with_guardrail
from core.models import AgentResult, EvaluationResult
from core.scoring import compute_final_score
from core.mlops import MLOpsTracker
from core.prompts import (
    STRUCTURE_PROMPT,
    SECURITY_PROMPT,
    SCALABILITY_PROMPT,
    PERFORMANCE_PROMPT,
    COST_PROMPT,
    REPORT_PROMPT,
)


def run_agent(
    system_prompt: str,
    dimension: str,
    user_input: str,
    tracker: MLOpsTracker
) -> AgentResult:
    """Run a single evaluation agent with RAG + guardrail + MLOps tracking."""

    # RAG — retrieve relevant best practices
    rag_context = retrieve(
        user_input,
        dimension=dimension,
        top_k=3
    )

    # Inject RAG context into prompt
    enriched_prompt = system_prompt + "\n\n" + rag_context

    start = time.time()
    success = True
    json_valid = True

    # Track the actual model used by this agent
    actual_model = "unknown"

    try:

        def call_fn(prompt, inp):
            nonlocal actual_model

            result, model, complexity = route(
                prompt,
                inp,
                expect_json=True,
                mlops_tracker=tracker
            )

            # Store the model actually used by this agent
            actual_model = model

            return result

        raw = run_with_guardrail(
            fn=call_fn,
            system_prompt=enriched_prompt,
            user_input=user_input,
            dimension=dimension
        )

        # Hallucination check
        tracker.check_hallucination(
            raw,
            user_input
        )

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

    # Log agent result using the actual model used
    tracker.log_agent(
        dimension=dimension,
        model=actual_model,
        latency=latency,
        success=success,
        json_valid=json_valid,
        score=agent_result.score
    )

    return agent_result


def generate_report(
    result: EvaluationResult,
    user_input: str,
    tracker: MLOpsTracker
) -> str:
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

        report, model, _ = route(
            REPORT_PROMPT,
            summary,
            expect_json=False,
            mlops_tracker=tracker
        )

        return report

    except Exception as e:

        return f"Report generation failed: {e}"


def evaluate(user_input: str) -> EvaluationResult:
    """
    Main ArchLens evaluation pipeline.

    Pipeline:
        Complexity classification
            ↓
        Parallel agents
            ↓
        RAG + LLM + Guardrail
            ↓
        Scoring
            ↓
        Final report
            ↓
        MLOps tracking
    """

    complexity = classify_complexity(user_input)

    tracker = MLOpsTracker(
        user_input=user_input,
        complexity=complexity
    )

    print(f"\nComplexity: {complexity}")

    agents = [
        (STRUCTURE_PROMPT, "structure"),
        (SECURITY_PROMPT, "security"),
        (SCALABILITY_PROMPT, "scalability"),
        (PERFORMANCE_PROMPT, "performance"),
        (COST_PROMPT, "cost"),
    ]

    results = {}

    # =========================================================
    # RUN FIVE AGENTS IN PARALLEL
    # =========================================================

    print("\nRunning evaluation agents in parallel...\n")

    with ThreadPoolExecutor(max_workers=5) as executor:

        futures = {
            executor.submit(
                run_agent,
                prompt,
                dimension,
                user_input,
                tracker
            ): dimension
            for prompt, dimension in agents
        }

        for future in as_completed(futures):

            dimension = futures[future]

            try:

                results[dimension] = future.result()

                print(
                    f"✓ {dimension.capitalize()} agent completed "
                    f"— score: {results[dimension].score}/10"
                )

            except Exception as e:

                print(
                    f"✗ {dimension.capitalize()} agent crashed: {e}"
                )

                results[dimension] = AgentResult(
                    dimension=dimension,
                    score=5.0,
                    issues=[],
                    recommendations=[],
                    summary=f"Evaluation error: {str(e)}"
                )

    # =========================================================
    # BUILD EVALUATION RESULT
    # =========================================================

    evaluation = EvaluationResult(
        **results
    )

    # =========================================================
    # CALCULATE FINAL SCORE
    # =========================================================

    evaluation.final_score = compute_final_score(
        evaluation
    )

    print(
        f"\nFinal weighted score: "
        f"{evaluation.final_score}/10"
    )

    # =========================================================
    # GENERATE FINAL REPORT
    # =========================================================

    print("Generating report...")

    evaluation.final_report = generate_report(
        evaluation,
        user_input,
        tracker
    )

    # =========================================================
    # SAVE MLOPS DATA
    # =========================================================

    tracker.save(
        result=evaluation
    )

    print(
        f"MLOps saved — evaluation id: "
        f"{tracker.evaluation_id}"
    )

    return evaluation

