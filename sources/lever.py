import requests
from models import Job

# Public Lever postings API:
# https://api.lever.co/v0/postings/{company}?mode=json

def fetch_lever(company: str) -> list[Job]:
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    jobs: list[Job] = []
    for item in data:
        jobs.append(Job(
            source="lever",
            source_id=str(item.get("id")),
            company=company,
            title=item.get("text",""),
            location=item.get("categories", {}).get("location","") or "",
            url=item.get("hostedUrl","") or "",
            description="",
            posted_at=item.get("createdAt") and str(item.get("createdAt"))
        ))
    return jobs
