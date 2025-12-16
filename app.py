import json
import re
import streamlit as st

from db import init_db, upsert_jobs, list_jobs, get_fit, save_fit
from sources.greenhouse import fetch_greenhouse
from sources.lever import fetch_lever
from sources.rss import fetch_rss
from llm_fit import analyze_fit

init_db()

st.set_page_config(page_title="Job Search Automator", layout="wide")
st.title("Job Search Automator (MVP)")

# --- Load config
st.sidebar.header("Config")
cfg_file = st.sidebar.file_uploader("Upload config JSON", type=["json"])
if cfg_file:
    cfg = json.load(cfg_file)
else:
    st.sidebar.info("Upload config JSON (see config.example.json).")
    cfg = None

resume_text = st.sidebar.text_area("Paste your resume text", height=250, placeholder="Paste resume here...")

def matches_filters(company, title, location, url, desc, keywords, titles, locations):
    hay = " ".join([company, title, location, url, desc]).lower()
    if titles:
        # pass if any title phrase matches
        if not any(t.lower() in title.lower() for t in titles):
            return False
    if locations:
        if not any(l.lower() in (location or "").lower() for l in locations):
            # allow remote keyword in description/title
            if not re.search(r"\bremote\b", hay):
                return False
    if keywords:
        if not any(k.lower() in hay for k in keywords):
            return False
    return True

colA, colB = st.columns([1, 2])

with colA:
    st.subheader("1) Ingest jobs")

    if st.button("Fetch from sources", disabled=(cfg is None)):
        jobs = []
        for b in cfg["sources"].get("greenhouse_boards", []):
            try:
                jobs += fetch_greenhouse(b)
            except Exception as e:
                st.warning(f"Greenhouse fetch failed for {b}: {e}")
        for c in cfg["sources"].get("lever_companies", []):
            try:
                jobs += fetch_lever(c)
            except Exception as e:
                st.warning(f"Lever fetch failed for {c}: {e}")
        for feed in cfg["sources"].get("rss_feeds", []):
            try:
                jobs += fetch_rss(feed, source_name="rss")
            except Exception as e:
                st.warning(f"RSS fetch failed for {feed}: {e}")

        inserted = upsert_jobs(jobs)
        st.success(f"Ingested {len(jobs)} jobs. New: {inserted}")

    st.subheader("2) Manual add (for LinkedIn/Indeed/Monster)")
    man_company = st.text_input("Company")
    man_title = st.text_input("Title")
    man_location = st.text_input("Location")
    man_url = st.text_input("URL (optional)")
    man_desc = st.text_area("Job description text", height=200)

    if st.button("Save manual job"):
        from models import Job
        j = Job(
            source="manual",
            source_id=man_url or f"{man_company}:{man_title}:{hash(man_desc)}",
            company=man_company or "manual",
            title=man_title,
            location=man_location,
            url=man_url,
            description=man_desc,
            posted_at=None
        )
        upsert_jobs([j])
        st.success("Saved.")

with colB:
    st.subheader("Jobs")

    rows = list_jobs()
    if cfg:
        keywords = cfg["search"].get("keywords", [])
        titles = cfg["search"].get("titles", [])
        locations = cfg["search"].get("locations", [])
    else:
        keywords, titles, locations = [], [], []

    filtered = []
    for r in rows:
        job_id, source, source_id, company, title, location, url, desc, posted_at = r
        if cfg:
            if not matches_filters(company, title, location or "", url or "", desc or "", keywords, titles, locations):
                continue
        filtered.append(r)

    st.write(f"Showing {len(filtered)} jobs (after filters).")

    for r in filtered[:50]:
        job_id, source, source_id, company, title, location, url, desc, posted_at = r
        with st.expander(f"{title} — {company} ({location}) [{source}]"):
            if url:
                st.markdown(f"**URL:** {url}")
            if desc:
                st.markdown("**Description (stored):**")
                st.write(desc[:3000])

            fit_row = get_fit(job_id)
            if fit_row:
                fit_score, recommend_apply, rationale, strengths, gaps, tailoring = fit_row
                st.markdown(f"### Fit: {fit_score:.1f}  |  Recommend apply: {'✅' if recommend_apply else '❌'}")
                st.write(rationale)
                st.markdown("**Resume tailoring:**")
                import json as _json
                for b in _json.loads(tailoring or "[]"):
                    st.write(f"- {b}")

            run_disabled = (not resume_text) or (not desc)
            if st.button(f"Run fit analysis for job #{job_id}", disabled=run_disabled):
                fit = analyze_fit(
                    resume_text=resume_text,
                    job_title=title,
                    job_location=location or "",
                    job_description=desc
                )
                save_fit(job_id, fit)
                st.success(f"Saved fit: {fit.fit_score:.1f}")
