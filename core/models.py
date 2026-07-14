from pydantic import BaseModel, Field
from typing import List
from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Issue(BaseModel):
    title: str
    description: str
    severity: Severity


class AgentResult(BaseModel):
    dimension: str
    score: float = Field(ge=0, le=10)
    issues: List[Issue]
    recommendations: List[str]
    summary: str


class EvaluationResult(BaseModel):
    structure: AgentResult
    security: AgentResult
    scalability: AgentResult
    performance: AgentResult
    cost: AgentResult
    final_score: float = 0.0
    final_report: str = ""