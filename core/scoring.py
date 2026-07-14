WEIGHTS = {
    "security": 0.30,
    "scalability": 0.25,
    "performance": 0.20,
    "cost": 0.15,
    "structure": 0.10,
}


def compute_final_score(result) -> float:
    scores = {
        "security": result.security.score,
        "scalability": result.scalability.score,
        "performance": result.performance.score,
        "cost": result.cost.score,
        "structure": result.structure.score,
    }
    final = sum(scores[dim] * WEIGHTS[dim] for dim in WEIGHTS)
    return round(final, 2)


def get_score_label(score: float) -> str:
    if score >= 8:
        return "Excellent"
    elif score >= 6:
        return "Good"
    elif score >= 4:
        return "Needs improvement"
    else:
        return "Critical issues found"