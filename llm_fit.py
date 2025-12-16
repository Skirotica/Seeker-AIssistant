from openai import OpenAI
from models import FitResult

client = OpenAI()

FIT_SCHEMA = {
  "name": "job_fit_result",
  "schema": {
    "type": "object",
    "additionalProperties": False,
    "properties": {
      "fit_score": { "type": "number", "minimum": 1, "maximum": 10 },
      "recommend_apply": { "type": "boolean" },
      "rationale": { "type": "string" },
      "strengths": { "type": "array", "items": { "type": "string" } },
      "gaps": { "type": "array", "items": { "type": "string" } },
      "resume_tailoring": { "type": "array", "items": { "type": "string" } }
    },
    "required": ["fit_score","recommend_apply","rationale","strengths","gaps","resume_tailoring"]
  },
  "strict": True
}

SYSTEM = """You are a job-fit analyst.
You must score fit from 1.0 to 10.0 (decimals allowed).
If fit_score < 7.0: set recommend_apply=false and keep strengths/gaps concise and resume_tailoring minimal.
If fit_score >= 7.0: set recommend_apply=true and produce strong resume_tailoring bullet suggestions specific to the job.
Be candid and non-sycophantic.
"""

def analyze_fit(resume_text: str, job_title: str, job_location: str, job_description: str) -> FitResult:
    user = f"""
RESUME:
{resume_text}

JOB:
Title: {job_title}
Location: {job_location}
Description:
{job_description}
"""
    resp = client.responses.create(
        model="gpt-5-mini",  # pick your preferred model
        input=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user}
        ],
        text={
            "format": {
                "type": "json_schema",
                "json_schema": FIT_SCHEMA
            }
        },
        temperature=0.2
    )
    # The SDK returns parsed JSON as text output content; simplest is to parse:
    import json
    content = resp.output_text
    data = json.loads(content)
    return FitResult(**data)
