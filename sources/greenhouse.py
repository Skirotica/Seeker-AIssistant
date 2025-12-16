import requests
from models import Job

# Public Greenhouse boards API (commonly used by companies)
# Example company_board_token is the part after /boards/ in many GH URLs, but not always.
# Endpoint: https://boards-api.greenhouse.io/v1/boards/{board}/jobs

def fetch_greenhouse(board: str) -> list[Job]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    jobs: list[Job] = []
    for item in data.get("jobs", []):
        jobs.append(Job(
            source="greenhouse",
            source_id=str(item.get("id")),
            company=board,
            title=item.get("title",""),
            location=(item.get("location") or {}).get("name",""),
            url=item.get("absolute_url",""),
            description="",
            posted_at=item.get("updated_at") or item.get("created_at")
  # sometimes available
        ))
    return jobs
