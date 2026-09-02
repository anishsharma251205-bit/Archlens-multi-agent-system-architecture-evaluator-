
import sqlite3
import time
import json
import statistics

from pathlib import Path
from datetime import datetime


DB_PATH = Path(__file__).parent.parent / "data" / "mlops.db"


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    """Initialize SQLite database for MLOps tracking."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            input_length INTEGER,
            complexity TEXT,
            model_used TEXT,
            latency_seconds REAL,
            structure_score REAL,
            security_score REAL,
            scalability_score REAL,
            performance_score REAL,
            cost_score REAL,
            final_score REAL,
            json_failed INTEGER DEFAULT 0,
            hallucination_flag INTEGER DEFAULT 0,
            error TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluation_id INTEGER,
            dimension TEXT,
            model TEXT,
            latency REAL,
            success INTEGER,
            json_valid INTEGER,
            score REAL,
            timestamp TEXT,
            FOREIGN KEY (evaluation_id) REFERENCES evaluations(id)
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# MLOPS TRACKER
# ============================================================

class MLOpsTracker:
    """Tracks all MLOps metrics for a single evaluation run."""

    def __init__(self, user_input: str, complexity: str):

        init_db()

        self.user_input = user_input
        self.complexity = complexity
        self.input_length = len(user_input.split())

        self.start_time = time.time()

        self.agent_logs = []
        self.json_failures = 0
        self.hallucination_flags = 0

        self.model_used = "mistral"
        self.evaluation_id = None

    def log_agent(
        self,
        dimension: str,
        model: str,
        latency: float,
        success: bool,
        json_valid: bool,
        score: float = 0.0,
    ):
        """Log individual agent call."""

        self.agent_logs.append({
            "dimension": dimension,
            "model": model,
            "latency": latency,
            "success": success,
            "json_valid": json_valid,
            "score": score,
            "timestamp": datetime.now().isoformat(),
        })

        if not json_valid:
            self.json_failures += 1

    def log(
        self,
        model: str,
        complexity: str,
        latency: float,
        success: bool,
    ):
        """Simple log for router calls."""

        self.model_used = model

    def check_hallucination(
        self,
        agent_output: dict,
        user_input: str,
    ) -> bool:
        """
        Simple hallucination check.

        Flags if an agent mentions more than three technologies
        that are not present in the original architecture input.
        """

        common_techs = [
            "kubernetes",
            "kafka",
            "redis",
            "elasticsearch",
            "mongodb",
            "postgresql",
            "mysql",
            "nginx",
            "docker",
            "aws",
            "gcp",
            "azure",
            "react",
            "vue",
            "angular",
            "node",
            "django",
            "flask",
            "fastapi",
            "graphql",
            "grpc",
            "rabbitmq",
            "sqs",
            "lambda",
            "ecs",
            "eks",
            "cloudfront",
            "s3",
            "rds",
        ]

        input_lower = user_input.lower()

        issues_text = " ".join(
            i.get("description", "")
            for i in agent_output.get("issues", [])
        ).lower()

        recommendations_text = " ".join(
            agent_output.get("recommendations", [])
        ).lower()

        full_output = issues_text + " " + recommendations_text

        hallucinated = []

        for tech in common_techs:
            if tech in full_output and tech not in input_lower:
                hallucinated.append(tech)

        if len(hallucinated) > 3:
            self.hallucination_flags += 1
            return True

        return False

    def save(self, result=None):
        """Save evaluation run to SQLite."""

        total_latency = time.time() - self.start_time

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        structure_score = result.structure.score if result else 0
        security_score = result.security.score if result else 0
        scalability_score = result.scalability.score if result else 0
        performance_score = result.performance.score if result else 0
        cost_score = result.cost.score if result else 0
        final_score = result.final_score if result else 0

        c.execute("""
            INSERT INTO evaluations (
                timestamp,
                input_length,
                complexity,
                model_used,
                latency_seconds,
                structure_score,
                security_score,
                scalability_score,
                performance_score,
                cost_score,
                final_score,
                json_failed,
                hallucination_flag
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            self.input_length,
            self.complexity,
            self.model_used,
            total_latency,
            structure_score,
            security_score,
            scalability_score,
            performance_score,
            cost_score,
            final_score,
            self.json_failures,
            self.hallucination_flags,
        ))

        self.evaluation_id = c.lastrowid

        for log in self.agent_logs:

            c.execute("""
                INSERT INTO agent_logs (
                    evaluation_id,
                    dimension,
                    model,
                    latency,
                    success,
                    json_valid,
                    score,
                    timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.evaluation_id,
                log["dimension"],
                log["model"],
                log["latency"],
                1 if log["success"] else 0,
                1 if log["json_valid"] else 0,
                log["score"],
                log["timestamp"],
            ))

        conn.commit()
        conn.close()

        return total_latency


# ============================================================
# METRICS
# ============================================================

def get_metrics() -> dict:
    """
    Compute all MLOps metrics from historical data.

    Returns:
        - total evaluations
        - average latency
        - JSON failure rate
        - hallucination rate
        - score deviation
        - MAE
        - accuracy
        - model usage
        - complexity distribution
        - complete evaluation history
        - mean score
    """

    init_db()

    conn = sqlite3.connect(DB_PATH)

    # Use Row objects so columns can be accessed by name.
    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    # --------------------------------------------------------
    # TOTAL EVALUATIONS
    # --------------------------------------------------------

    c.execute("""
        SELECT COUNT(*) AS total
        FROM evaluations
    """)

    total = c.fetchone()["total"]

    if total == 0:
        conn.close()

        return {
            "total_evaluations": 0
        }

    # --------------------------------------------------------
    # AVERAGE LATENCY
    # --------------------------------------------------------

    c.execute("""
        SELECT AVG(latency_seconds) AS avg_latency
        FROM evaluations
    """)

    row = c.fetchone()

    avg_latency = row["avg_latency"] or 0

    # --------------------------------------------------------
    # JSON FAILURE RATE
    # --------------------------------------------------------

    c.execute("""
        SELECT
            SUM(json_failed) AS failures,
            COUNT(*) AS total
        FROM evaluations
    """)

    row = c.fetchone()

    json_failures = row["failures"] or 0
    json_total = row["total"] or 1

    json_failure_rate = json_failures / max(json_total, 1)

    # --------------------------------------------------------
    # HALLUCINATION RATE
    # --------------------------------------------------------

    c.execute("""
        SELECT
            SUM(hallucination_flag) AS hallucinations,
            COUNT(*) AS total
        FROM evaluations
    """)

    row = c.fetchone()

    hallucinations = row["hallucinations"] or 0
    hallucination_total = row["total"] or 1

    hallucination_rate = (
        hallucinations / max(hallucination_total, 1)
    )

    # --------------------------------------------------------
    # SCORES
    # --------------------------------------------------------

    c.execute("""
        SELECT final_score
        FROM evaluations
        WHERE final_score > 0
    """)

    score_rows = c.fetchall()

    scores = [
        row["final_score"]
        for row in score_rows
        if row["final_score"] is not None
    ]

    # --------------------------------------------------------
    # SCORE DEVIATION
    # --------------------------------------------------------

    score_deviation = (
        statistics.stdev(scores)
        if len(scores) > 1
        else 0
    )

    # --------------------------------------------------------
    # MEAN SCORE
    # --------------------------------------------------------

    mean_score = (
        statistics.mean(scores)
        if scores
        else 0
    )

    # --------------------------------------------------------
    # MAE
    # --------------------------------------------------------

    mae = (
        statistics.mean(
            [
                abs(score - mean_score)
                for score in scores
            ]
        )
        if scores
        else 0
    )

    # --------------------------------------------------------
    # ACCURACY
    # --------------------------------------------------------

    accuracy = (
        sum(
            1
            for score in scores
            if abs(score - mean_score) <= 1.0
        )
        / max(len(scores), 1)
    )

    # --------------------------------------------------------
    # MODEL USAGE
    # --------------------------------------------------------

    c.execute("""
        SELECT
            model_used,
            COUNT(*) AS cnt
        FROM evaluations
        GROUP BY model_used
    """)

    model_usage = {
        row["model_used"]: row["cnt"]
        for row in c.fetchall()
    }

    # --------------------------------------------------------
    # COMPLEXITY DISTRIBUTION
    # --------------------------------------------------------

    c.execute("""
        SELECT
            complexity,
            COUNT(*) AS cnt
        FROM evaluations
        GROUP BY complexity
    """)

    complexity_dist = {
        row["complexity"]: row["cnt"]
        for row in c.fetchall()
    }

    # --------------------------------------------------------
    # COMPLETE EVALUATION HISTORY
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # Previously this returned only the last 10 runs.
    # Now it returns ALL evaluations.
    #

    c.execute("""
        SELECT
            id,
            timestamp,
            final_score,
            complexity
        FROM evaluations
        ORDER BY id DESC
    """)

    evaluation_rows = c.fetchall()

    recent = [
        {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "score": row["final_score"],
            "complexity": row["complexity"],
        }
        for row in evaluation_rows
    ]

    # --------------------------------------------------------
    # CLOSE DATABASE
    # --------------------------------------------------------

    conn.close()

    # --------------------------------------------------------
    # RETURN METRICS
    # --------------------------------------------------------

    return {
        "total_evaluations": total,
        "avg_latency_seconds": round(avg_latency, 2),
        "json_failure_rate": round(json_failure_rate, 4),
        "hallucination_rate": round(hallucination_rate, 4),
        "score_deviation": round(score_deviation, 4),
        "mae": round(mae, 4),
        "accuracy": round(accuracy, 4),
        "model_usage": model_usage,
        "complexity_distribution": complexity_dist,
        "recent_evaluations": recent,
        "mean_score": round(mean_score, 2),
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    metrics = get_metrics()

    print(
        json.dumps(
            metrics,
            indent=2
        )
    )

