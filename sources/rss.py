import feedparser
from models import Job

def fetch_rss(feed_url: str, source_name: str = "rss") -> list[Job]:
    feed = feedparser.parse(feed_url)
    jobs: list[Job] = []
    for entry in feed.entries[:200]:
        jobs.append(Job(
            source=source_name,
            source_id=getattr(entry, "id", None) or getattr(entry, "link", ""),
            company=source_name,
            title=getattr(entry, "title", ""),
            location="",
            url=getattr(entry, "link", ""),
            description=getattr(entry, "summary", "") or "",
            posted_at=getattr(entry, "published", None)
        ))
    return jobs
