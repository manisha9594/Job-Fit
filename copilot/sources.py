"""Read-only job listing connectors.

Pull-only: free official APIs (Adzuna, Remotive, Arbeitnow, USAJobs) and
public JSON feeds for Greenhouse / Lever / Ashby-hosted career pages.

Deliberately NOT included: LinkedIn, Indeed, ZipRecruiter — their terms
prohibit bots that log in or apply automatically, and they actively detect
them. For those sites, paste a job link/description into the JD intake
instead; you do the applying yourself.
"""
import httpx

TIMEOUT = 20.0


def _listing(source: str, title: str, company: str, location: str = "",
             url: str = "", description: str = "", posted_at: str = "") -> dict:
    return {
        "source": source, "title": title or "", "company": company or "",
        "location": location or "", "url": url or "",
        "description": (description or "")[:2000], "posted_at": posted_at or "",
    }


def fetch_remotive(query: str = "", limit: int = 20) -> list[dict]:
    """Remotive remote-jobs API — no key required."""
    params = {"limit": limit}
    if query:
        params["search"] = query
    r = httpx.get("https://remotive.com/api/remote-jobs", params=params,
                  timeout=TIMEOUT)
    r.raise_for_status()
    jobs = r.json().get("jobs", [])
    return [_listing("remotive", j.get("title"), j.get("company_name"),
                     j.get("candidate_required_location", ""),
                     j.get("url", ""), j.get("description", ""),
                     j.get("publication_date", ""))
            for j in jobs[:limit]]


def fetch_arbeitnow(limit: int = 20) -> list[dict]:
    """Arbeitnow job-board API — no key required."""
    r = httpx.get("https://www.arbeitnow.com/api/job-board-api", timeout=TIMEOUT)
    r.raise_for_status()
    jobs = r.json().get("data", [])
    out = []
    for j in jobs[:limit]:
        loc = j.get("location", "") or ""
        if isinstance(loc, list):
            loc = ", ".join(loc)
        out.append(_listing("arbeitnow", j.get("title"), j.get("company_name"),
                            loc, j.get("url", ""), j.get("description", ""),
                            j.get("created_at", "")))
    return out


def fetch_adzuna(app_id: str, app_key: str, query: str = "",
                 country: str = "us", limit: int = 20) -> list[dict]:
    """Adzuna jobs API — free app_id/app_key from https://developer.adzuna.com."""
    if not app_id or not app_key:
        raise ValueError("Adzuna needs ADZUNA_APP_ID and ADZUNA_APP_KEY")
    r = httpx.get(
        f"https://api.adzuna.com/v1/api/jobs/{country}/search/1",
        params={"app_id": app_id, "app_key": app_key,
                "what": query, "results_per_page": limit,
                "content-type": "application/json"},
        timeout=TIMEOUT)
    r.raise_for_status()
    jobs = r.json().get("results", [])
    return [_listing("adzuna", j.get("title"),
                     (j.get("company") or {}).get("display_name", ""),
                     (j.get("location") or {}).get("display_name", ""),
                     j.get("redirect_url", ""), j.get("description", ""),
                     j.get("created", ""))
            for j in jobs[:limit]]


def fetch_usajobs(api_key: str, keyword: str,
                  location: str = "United States") -> list[dict]:
    """USAJobs search API — free key from https://developer.usajobs.gov."""
    if not api_key:
        raise ValueError("USAJobs needs USAJOBS_API_KEY")
    r = httpx.get(
        "https://data.usajobs.gov/api/search",
        params={"Keyword": keyword, "LocationName": location,
                "ResultsPerPage": 25},
        headers={"Authorization-Key": api_key,
                 "User-Agent": "job-search-copilot (portfolio demo)",
                 "Host": "data.usajobs.gov"},
        timeout=TIMEOUT)
    r.raise_for_status()
    items = r.json().get("SearchResult", {}).get("SearchResultItems", [])
    out = []
    for item in items:
        d = item.get("MatchedObjectDescriptor", {})
        out.append(_listing(
            "usajobs", d.get("PositionTitle"),
            d.get("OrganizationName", ""),
            d.get("PositionLocationDisplay", ""),
            d.get("PositionURI", ""),
            (d.get("UserArea", {}).get("Details", {}).get("JobSummary", "")),
            d.get("PublicationStartDate", "")))
    return out


def fetch_greenhouse(board_token: str, limit: int = 50) -> list[dict]:
    """Greenhouse public boards API — no key. board_token is the company's
    board slug, e.g. 'openai' in boards.greenhouse.io/openai."""
    r = httpx.get(f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs",
                  timeout=TIMEOUT)
    r.raise_for_status()
    jobs = r.json().get("jobs", [])
    return [_listing("greenhouse", j.get("title"), board_token,
                     (j.get("location") or {}).get("name", ""),
                     j.get("absolute_url", ""), "",
                     j.get("updated_at", ""))
            for j in jobs[:limit]]


def fetch_lever(company: str, limit: int = 50) -> list[dict]:
    """Lever public postings API — no key. company is the Lever slug,
    e.g. 'netflix' in jobs.lever.co/netflix."""
    r = httpx.get(f"https://api.lever.co/v0/postings/{company}",
                  params={"mode": "json"}, timeout=TIMEOUT)
    r.raise_for_status()
    jobs = r.json() if isinstance(r.json(), list) else []
    return [_listing("lever", j.get("text"), company,
                     (j.get("categories") or {}).get("location", ""),
                     j.get("hostedUrl", ""), j.get("descriptionPlain", ""),
                     j.get("createdAt", ""))
            for j in jobs[:limit]]


def fetch_ashby(board: str, limit: int = 50) -> list[dict]:
    """Ashby public posting API — no key. board is the Ashby board slug."""
    r = httpx.get(f"https://api.ashbyhq.com/posting-api/job-board/{board}",
                  timeout=TIMEOUT)
    r.raise_for_status()
    jobs = r.json().get("jobs", [])
    return [_listing("ashby", j.get("title"), board,
                     j.get("locationName", ""),
                     j.get("jobUrl", ""), "",
                     j.get("publishedAt", ""))
            for j in jobs[:limit]]


def search(source: str, **kwargs) -> list[dict]:
    """Dispatch to one connector by name."""
    handlers = {
        "remotive": fetch_remotive,
        "arbeitnow": fetch_arbeitnow,
        "adzuna": fetch_adzuna,
        "usajobs": fetch_usajobs,
        "greenhouse": fetch_greenhouse,
        "lever": fetch_lever,
        "ashby": fetch_ashby,
    }
    if source not in handlers:
        raise ValueError(f"unknown source {source!r}; choose from {sorted(handlers)}")
    return handlers[source](**kwargs)
