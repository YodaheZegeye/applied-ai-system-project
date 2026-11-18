"""
Agentic RAG workflow:
  natural language → extract profile → build search query
  → iTunes worldwide search → Gemini ranks & explains → Gemini summary
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

from google import genai

from src.itunes import search_songs

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-3.8-flash"

AVAILABLE_GENRES = [
    "pop", "rock", "hip-hop/rap", "r&b/soul", "electronic", "dance",
    "jazz", "classical", "country", "folk", "metal", "lofi",
    "reggae", "blues", "indie", "alternative", "ambient",
]
AVAILABLE_MOODS = [
    "happy", "chill", "intense", "euphoric", "moody", "confident",
    "romantic", "peaceful", "angry", "nostalgic", "focused",
    "melancholic", "relaxed", "uplifting", "energetic",
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AgentStep:
    name: str
    input: str
    output: str


@dataclass
class AgentResult:
    user_input: str
    extracted_profile: dict
    search_query: str
    recommendations: List[dict]
    summary: str
    steps: List[AgentStep] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set. Add it to your .env file.")
    return genai.Client(api_key=api_key)


def _extract_json(text: str):
    """Robustly pull the first JSON value out of a model response."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return json.loads(match.group(1))
    # Try JSON object
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group(0))
    # Try JSON array
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"Could not parse JSON from: {text[:300]}")


# ---------------------------------------------------------------------------
# Agent steps
# ---------------------------------------------------------------------------

def extract_profile_and_query(client: genai.Client, user_input: str) -> tuple:
    """
    Gemini call 1 of 2.
    Extracts the preference profile AND builds the iTunes search query in one shot.
    """
    prompt = f"""You are a music preference parser and iTunes search query builder.

User description: "{user_input}"

Mood options: {", ".join(AVAILABLE_MOODS)}

Return ONLY a JSON object:
{{
  "genre": "<a common iTunes genre name that best fits>",
  "mood": "<one mood from the list>",
  "target_energy": <float 0.0–1.0, where 0=very calm, 1=very intense>,
  "reasoning": "<one sentence>",
  "search_query": "<2–5 word iTunes search query that will surface this type of music>"
}}"""

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    logger.debug(f"extract_profile_and_query raw: {response.text[:200]}")

    data = _extract_json(response.text)
    for key in ("genre", "mood", "target_energy", "search_query"):
        if key not in data:
            raise ValueError(f"Missing required field: '{key}'")

    data["target_energy"] = max(0.0, min(1.0, float(data["target_energy"])))
    profile = {k: data[k] for k in ("genre", "mood", "target_energy", "reasoning")}
    query = data["search_query"].strip().strip("\"'")
    logger.info(f"Profile + query | {profile} | query='{query}'")
    return profile, query


def rank_and_summarize(
    client: genai.Client,
    user_input: str,
    profile: dict,
    candidates: List[dict],
) -> tuple:
    """
    Gemini call 2 of 2.
    Picks the top 5 songs AND writes the summary intro in one shot.
    """
    if not candidates:
        raise ValueError("No songs returned from iTunes.")

    catalog_text = "\n".join(
        f"{i + 1}. \"{s['title']}\" by {s['artist']} "
        f"(genre: {s['genre']}, album: {s['album']})"
        for i, s in enumerate(candidates)
    )

    prompt = f"""You are a music recommendation expert with deep knowledge of worldwide music.

User asked for: "{user_input}"
Profile: genre={profile['genre']}, mood={profile['mood']}, energy={profile['target_energy']}

Here are {len(candidates)} songs from a live iTunes search:
{catalog_text}

Do both tasks in one response:
1. Pick the 5 best matches. Write one sentence per song explaining why it fits.
2. Write a warm 2–3 sentence intro (under 70 words) for the final picks.

Return ONLY a JSON object:
{{
  "picks": [
    {{"index": <1-based number from list>, "reason": "<one sentence>"}},
    {{"index": ..., "reason": "..."}},
    {{"index": ..., "reason": "..."}},
    {{"index": ..., "reason": "..."}},
    {{"index": ..., "reason": "..."}}
  ],
  "summary": "<warm 2–3 sentence intro>"
}}"""

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    logger.debug(f"rank_and_summarize raw: {response.text[:300]}")

    data = _extract_json(response.text)
    picks = data.get("picks", [])
    summary = data.get("summary", "Here are your top picks.")

    ranked = []
    seen = set()
    for item in picks:
        idx = int(item["index"]) - 1
        if 0 <= idx < len(candidates) and idx not in seen:
            song = dict(candidates[idx])
            song["reason"] = item.get("reason", "Selected for you.")
            ranked.append(song)
            seen.add(idx)
        if len(ranked) == 5:
            break

    if len(ranked) < 5:
        for i, s in enumerate(candidates):
            if i not in seen:
                song = dict(s)
                song["reason"] = "Selected to complete your top 5."
                ranked.append(song)
                seen.add(i)
            if len(ranked) == 5:
                break

    return ranked, summary


# ---------------------------------------------------------------------------
# Main agent loop
# ---------------------------------------------------------------------------

def run_agent(user_input: str) -> AgentResult:
    """
    Full RAG agentic loop (2 Gemini calls):
      [Call 1] extract profile + build query
      search iTunes worldwide
      [Call 2] rank top 5 + generate summary
    """
    client = get_client()
    steps: List[AgentStep] = []
    logger.info(f"Agent started | input='{user_input}'")

    # Gemini call 1 — profile + query
    profile, query = extract_profile_and_query(client, user_input)
    steps.append(AgentStep(
        name="Extract Profile & Query",
        input=user_input,
        output=(
            f"genre={profile['genre']}, mood={profile['mood']}, "
            f"energy={profile['target_energy']:.2f} | "
            f"query=\"{query}\""
        ),
    ))

    # iTunes search
    candidates = search_songs(query, limit=30)
    if not candidates:
        fallback = profile["genre"]
        logger.warning(f"No results for '{query}', retrying with '{fallback}'")
        candidates = search_songs(fallback, limit=30)
        steps.append(AgentStep(
            name="iTunes Search (fallback)",
            input=f"'{query}' returned 0 results",
            output=f"Retried with '{fallback}' → {len(candidates)} songs",
        ))
    else:
        steps.append(AgentStep(
            name="iTunes Search",
            input=f"query=\"{query}\"",
            output=f"Retrieved {len(candidates)} songs from Apple's worldwide catalog",
        ))

    if not candidates:
        raise RuntimeError(
            "iTunes returned no results. Check your connection or try a different description."
        )

    # Gemini call 2 — rank + summarize
    ranked, summary = rank_and_summarize(client, user_input, profile, candidates)
    steps.append(AgentStep(
        name="Rank & Summarize",
        input=f"{len(candidates)} candidates",
        output=f"Top pick: \"{ranked[0]['title']}\" by {ranked[0]['artist']}",
    ))
    logger.info(f"Agent done | top='{ranked[0]['title']}'")

    return AgentResult(
        user_input=user_input,
        extracted_profile=profile,
        search_query=query,
        recommendations=ranked,
        summary=summary,
        steps=steps,
    )
