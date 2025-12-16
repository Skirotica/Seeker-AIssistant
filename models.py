from pydantic import BaseModel, Field
from typing import List, Optional


class Job(BaseModel):
    source: str
    source_id: str
    company: str
    title: str
    location: str = ""
    url: str = ""
    description: str = ""
    posted_at: Optional[str] = None


class FitResult(BaseModel):
    fit_score: float = Field(..., ge=1.0, le=10.0)
    recommend_apply: bool
    rationale: str
    strengths: List[str] = []
    gaps: List[str] = []
    resume_tailoring: List[str] = []
