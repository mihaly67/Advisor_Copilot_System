from dataclasses import dataclass
@dataclass
class TaskClassification:
    is_local_capable: bool
    task: str
    estimated_tokens: int
    complexity_score: float
    confidence: float
    recommended_mode: str
    reasoning: str
