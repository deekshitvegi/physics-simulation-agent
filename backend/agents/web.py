"""Web research helpers: DuckDuckGo search + page/PDF text extraction.

Used by the tutor's `search_web` / `fetch_url` tools so it can find and read
published solutions to known problems (e.g. JEE past papers).
"""
from __future__ import annotations

import io

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS
from pypdf import PdfReader

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PhysicsTutorBot/1.0)"}


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Return search hits as [{title, url, snippet}]."""
    hits = DDGS().text(query, max_results=max_results)
    return [
        {
            "title": h.get("title", ""),
            "url": h.get("href", ""),
            "snippet": h.get("body", ""),
        }
        for h in hits
    ]


def fetch_page(url: str, max_chars: int = 6000) -> str:
    """Fetch a URL and return readable text (handles HTML and PDF)."""
    with httpx.Client(timeout=15.0, follow_redirects=True, headers=_HEADERS) as client:
        resp = client.get(url)
        resp.raise_for_status()
        ctype = resp.headers.get("content-type", "").lower()

        if "pdf" in ctype or url.lower().split("?")[0].endswith(".pdf"):
            reader = PdfReader(io.BytesIO(resp.content))
            text = "\n".join((page.extract_text() or "") for page in reader.pages[:15])
        else:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)

    text = " ".join(text.split())
    return text[:max_chars]
