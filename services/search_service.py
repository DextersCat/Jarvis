import asyncio
import json
import logging
import os
import urllib.parse
import urllib.request
from typing import Dict, List

logger = logging.getLogger(__name__)

API_TIMEOUT_SECONDS = 8


def _get_google_credentials():
    return os.getenv("GOOGLE_SEARCH_API_KEY"), os.getenv("GOOGLE_SEARCH_CX")


def _parse_results(items: List[dict], limit: int) -> List[Dict[str, str]]:
    results = []
    for item in items[:limit]:
        results.append(
            {
                "title": item.get("title", ""),
                "snippet": item.get("snippet") or item.get("htmlSnippet", ""),
                "url": item.get("link", ""),
            }
        )
    return results


def _build_request_url(query: str, num_results: int) -> str:
    key, cx = _get_google_credentials()
    params = {
        "q": query,
        "key": key or "",
        "cx": cx or "",
        "num": max(1, min(num_results, 10)),
    }
    encoded = urllib.parse.urlencode(params)
    return f"https://www.googleapis.com/customsearch/v1?{encoded}"


def _make_request(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "JarvisWebSearch/1.0"})
    with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as response:
        payload = response.read()
    return json.loads(payload.decode("utf-8"))


async def search_web(query: str, num_results: int = 5) -> dict:
    """
    Call Google Programmable Search (CSE) with the given query.
    Return {"query": str, "results": [{"title": str, "snippet": str, "url": str}, ...]}.
    Handle HTTP/network errors gracefully and return an empty 'results' list on failure.
    """

    trimmed = (query or "").strip()
    if not trimmed:
        return {"query": query, "results": []}

    api_key, cx = _get_google_credentials()
    if not api_key or not cx:
        logger.warning("Google Search CSE credentials missing; returning no results.")
        return {"query": query, "results": []}

    url = _build_request_url(trimmed, num_results)

    try:
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, _make_request, url)
        items = data.get("items", []) if isinstance(data, dict) else []
        results = _parse_results(items, num_results)
        return {"query": query, "results": results}
    except Exception as exc:
        logger.exception("Web search failed: %s", exc)
        return {"query": query, "results": []}


async def summarise_search_results(llm_client, query: str, results: List[dict]) -> str:
    """
    Use the existing Jarvis LLM pipeline (LLaMA3 via Ollama) to generate a 2–4 sentence spoken summary
    plus a few bullet points. The returned string should be suitable for both TTS and markdown.
    """

    clean_query = (query or "").strip()
    safe_results = results or []

    if not safe_results:
        return f"I couldn't retrieve web results for '{clean_query}'."

    bullet_lines = []
    for idx, item in enumerate(safe_results[:5], start=1):
        title = item.get("title", "(no title)")
        url = item.get("url", "")
        bullet_lines.append(f"{idx}. {title} — {url}")

    prompt = (
        "You are Jarvis generating a concise spoken recap of web search results. "
        "Provide 2-4 sentences that sound natural when read aloud, followed by 2-4 bullet points. "
        "Keep it factual and avoid speculation. "
        "Keep the whole reply tight for TTS and end with: 'Let me know if you'd like more detail, Sir.'"
    )

    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                f"Query: {clean_query}\n"
                f"Top results:\n" + "\n".join(bullet_lines)
            ),
        },
    ]

    try:
        completion = await asyncio.to_thread(
            llm_client.chat.completions.create,
            model="llama3",
            messages=messages,
        )
        return completion.choices[0].message.content
    except Exception as exc:
        logger.exception("LLM summary generation failed: %s", exc)
        return "Summary unavailable due to an internal error."
