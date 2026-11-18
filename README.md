# AI Music Recommender

An agentic AI system that searches Apple's worldwide iTunes catalog based on a natural language description of what you want to hear. Built as an evolution of a content-based music recommender simulation from Modules 1–3.

---

## Original Project

**Module 1–3 Project: Music Recommender Simulation**

The original project was a content-based music recommender that scored 18 hardcoded songs stored in a CSV file against a manually constructed user profile using a weighted formula: genre match (+2.0), mood match (+1.0), and energy proximity (0–1.0). It ran entirely from the command line, required the user to supply structured preference data as a Python dict, and had no AI components. Its purpose was to simulate how real-world recommenders like Spotify work at a small scale.

---

## Title and Summary

**AI Music Recommender** turns a plain English description into real song recommendations pulled live from Apple's iTunes worldwide catalog. You type something like *"upbeat Afrobeats for a party"* and the system uses Google Gemini AI to understand what you mean, searches iTunes for matching songs, and returns five picks with album artwork, a playable 30-second preview, and a link to Apple Music. It matters because it demonstrates how agentic AI and retrieval-augmented generation (RAG) can replace brittle, hardcoded systems with something that understands natural language and pulls from a live, real-world data source.

---

## Architecture Overview

The system follows a five-step RAG agentic loop using exactly two Gemini API calls:

1. **Extract + Query (Gemini call 1):** The user's plain English input is sent to Gemini, which extracts a structured preference profile (genre, mood, energy level) and builds an optimized iTunes search query — all in one call.

2. **Retrieve (iTunes API):** The search query is sent to Apple's iTunes Search API, which returns up to 30 real songs from its worldwide catalog. No API key required.

3. **Rank + Summarize (Gemini call 2):** All 30 candidate songs are sent to Gemini, which picks the best 5, writes a one-sentence reason for each, and generates a friendly summary paragraph — all in one call.

4. **Display:** Results appear in a Streamlit web UI with album artwork, playable audio previews, and Apple Music links.

5. **Testing:** A separate pytest suite with 13 tests validates the original scoring engine (`src/recommender.py`) independently of the live AI and API calls.

See `diagrams/architecture.mmd` for the full system diagram.

---

## Setup Instructions

**Requirements:** Python 3.10+, a Google Gemini API key, internet connection.

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/applied-ai-system-project.git
cd applied-ai-system-project
```

**2. Create and activate a virtual environment**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up your API key**

Create a file called `.env` in the project root:
```
GEMINI_API_KEY=your_gemini_api_key_here
```
Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).

**5. Run the app**
```bash
streamlit run app.py
```
The app will open in your browser at `http://localhost:8501`.

**6. Run the tests**
```bash
pytest
```
Expected output: `13 passed`.

---

## Sample Interactions

### Example 1 — Afrobeats Party

**Input:** `upbeat Afrobeats for a party`

**Agent extracted:**
- Genre: Afrobeats · Mood: energetic · Energy: 0.90
- iTunes query: `"afrobeats party dance"`

**Top picks returned:**
1. **Essence** — Wizkid ft. Tems · *Reason: High-energy Afrobeats anthem perfect for a party atmosphere.*
2. **Last Last** — Burna Boy · *Reason: Infectious rhythm and upbeat production make this a crowd favourite.*
3. **Fall** — Davido · *Reason: Smooth yet energetic Afrobeats track guaranteed to get people moving.*
4. **Mood** — Oxlade · *Reason: Contemporary Afrobeats with an irresistible danceable groove.*
5. **Ke Star** — Focalistic · *Reason: Amapiano-Afrobeats fusion with the energy a party needs.*

**Summary:** *"Here are five tracks that will keep any party going. From Wizkid's global hit to Burna Boy's infectious rhythms, this playlist covers the best of modern Afrobeats — high energy, great vibes, and impossible not to dance to."*

---

### Example 2 — Rainy Day Study Session

**Input:** `chill lofi beats to study on a rainy afternoon`

**Agent extracted:**
- Genre: Electronic · Mood: focused · Energy: 0.25
- iTunes query: `"lofi chill study beats"`

**Top picks returned:**
1. **Snowfall** — Øneheart & reidenshi · *Reason: Dreamy, low-tempo lofi track ideal for deep focus.*
2. **River** — Yaeow · *Reason: Gentle piano loops and soft beats create a calm study environment.*
3. **Feather** — Nujabes · *Reason: Iconic lofi jazz-hop that has soundtracked study sessions worldwide.*
4. **Alone Pt. II** — Ikson · *Reason: Minimal and soothing — keeps you in flow without distraction.*
5. **Rainfall** — The Ambientalist · *Reason: Perfectly pairs with a rainy day, blending ambient textures with soft rhythm.*

**Summary:** *"These five tracks are designed for focus and calm. Soft melodies, unhurried rhythms, and minimal lyrics make them ideal companions for a productive rainy afternoon study session."*

---

### Example 3 — 90s Hip-Hop Classics

**Input:** `classic 90s hip hop with hard beats`

**Agent extracted:**
- Genre: Hip-Hop/Rap · Mood: confident · Energy: 0.80
- iTunes query: `"90s hip hop classic rap"`

**Top picks returned:**
1. **Juicy** — The Notorious B.I.G. · *Reason: Defining 90s hip-hop anthem with iconic production and confident storytelling.*
2. **California Love** — 2Pac ft. Dr. Dre · *Reason: Hard-hitting West Coast classic with an undeniable beat.*
3. **Hard Knock Life** — Jay-Z · *Reason: Powerful 90s production with Jay-Z at his most confident.*
4. **C.R.E.A.M.** — Wu-Tang Clan · *Reason: Raw, gritty East Coast production that defined an era.*
5. **Regulate** — Warren G & Nate Dogg · *Reason: Smooth yet hard-hitting West Coast classic.*

**Summary:** *"These five tracks represent the golden era of hip-hop — confident lyrics, hard-hitting beats, and timeless production. Whether you're a longtime fan or discovering it for the first time, this is 90s rap at its finest."*

---

## Design Decisions

**Why replace the CSV with iTunes?**
The original 18-song CSV was a closed, static system. If a user asked for K-pop or Amapiano, there were no matches. iTunes gives access to millions of real songs from every genre and country, making the system genuinely useful for any music preference.

**Why two Gemini calls instead of four?**
The first version made four sequential Gemini calls (extract profile, build query, rank songs, write summary), which took 8–12 seconds. By merging profile extraction with query building (same input) and ranking with summarizing (same context), we cut it to two calls and roughly halved the latency to 3–5 seconds.

**Why Streamlit?**
Streamlit's `st.status()` component allows live step-by-step progress updates, which makes the wait feel shorter and shows the agentic workflow transparently. The card layout with `st.audio()` and `st.image()` made it easy to display album artwork and playable previews without a custom frontend.

**Why keep `src/recommender.py`?**
The original scoring engine was preserved to maintain the testing baseline and to demonstrate the evolution from rule-based scoring to AI-based ranking. Its 13 tests also satisfy the reliability/testing requirement from the rubric independently of live API calls.

**Trade-off: iTunes vs. Spotify**
iTunes requires no API key and no OAuth, making setup trivial. Spotify's API would provide richer metadata (actual audio features like energy and danceability) but requires account registration, OAuth flow, and rate limit management — too much friction for a project where setup simplicity matters.

---

## Testing Summary

**Testing methods used:** Automated unit tests · Logging & error handling · Human evaluation

---

### 1. Automated Tests — `pytest` (13 tests, all passing)

```
pytest tests/ -v
13 passed in 1.09s
```

Tests live in `tests/test_core.py` and cover the three functions the app calls on every single run — no internet connection or API key required.

**`_extract_json()` — parses Gemini responses robustly (6 tests)**

| Test | What it checks |
|---|---|
| `test_extract_json_clean_string` | Parses a plain JSON string correctly |
| `test_extract_json_wrapped_in_code_block` | Extracts JSON from a ```json code block |
| `test_extract_json_embedded_in_prose` | Pulls JSON out of surrounding prose text |
| `test_extract_json_parses_array` | Handles JSON arrays as well as objects |
| `test_extract_json_raises_on_garbage_input` | Raises `ValueError` on completely invalid input |
| `test_extract_json_handles_extra_whitespace` | Tolerates leading/trailing whitespace |

**`get_client()` — API key guard (1 test)**

| Test | What it checks |
|---|---|
| `test_get_client_raises_without_api_key` | Raises `ValueError` with a clear message when `GEMINI_API_KEY` is not set |

**`_parse_itunes_results()` — cleans raw iTunes API responses (6 tests)**

| Test | What it checks |
|---|---|
| `test_parse_itunes_returns_songs` | Correctly maps iTunes fields to app song dicts |
| `test_parse_itunes_filters_out_non_songs` | Drops music videos and podcasts, keeps only songs |
| `test_parse_itunes_upgrades_artwork_resolution` | Replaces 100×100 artwork URL with 300×300 |
| `test_parse_itunes_handles_missing_fields_gracefully` | Falls back to "Unknown" when iTunes omits fields |
| `test_parse_itunes_empty_list_returns_empty` | Returns an empty list without crashing |
| `test_parse_itunes_no_artwork_upgrade_when_blank` | Leaves blank artwork URL unchanged |

---

### 2. Logging & Error Handling

Every agent run is logged to `logs/agent_YYYYMMDD.log`. Sample log output:

```
2026-11-18 00:41:22 | INFO | src.agent | Agent started | input='afrobeats party'
2026-11-18 00:41:24 | INFO | src.agent | Profile + query | genre=Afrobeats | query='afrobeats dance party'
2026-11-18 00:41:24 | INFO | src.itunes | iTunes returned 28 songs
2026-11-18 00:41:26 | INFO | src.agent | Agent done | top='Ke Star' by Focalistic
```

Guardrails in place: missing API key caught at startup, energy values clamped to 0–1, iTunes returning zero results triggers an automatic fallback search before surfacing an error to the user.

---

### 3. Human Evaluation

Seven representative inputs were tested manually and evaluated against defined criteria:

| Test Input | Evaluation Criteria | Result |
|---|---|---|
| `"chill lofi music to study"` | Returns calm, low-energy lofi/electronic songs | Pass |
| `"upbeat Afrobeats for a party"` | Returns high-energy African/dance songs | Pass |
| `"k-pop workout songs"` | Returns K-pop songs; handles non-standard iTunes genre | Pass |
| `"90s hip hop classics"` | Returns recognizable 90s rap/hip-hop artists | Pass |
| `"musica romantica"` | Handles non-English input, returns romantic music | Pass |
| `""` (empty input) | UI shows warning, does not crash or call API | Pass |
| `"heavy metal relaxing ambient"` | Handles conflicting keywords gracefully | Partial — returned metal over ambient; genre weight dominates |

**Overall:** 6 out of 7 tests passed fully. The one partial case exposed a known limitation: when the user provides conflicting keywords, Gemini tends to favour the genre signal over the mood/energy signals, surfacing louder songs than intended.

---

**What was learned:**
Reducing API round trips (from 4 calls to 2) has a larger impact on perceived speed than optimizing any individual call. Showing live progress with `st.status()` made the remaining wait feel shorter even when total time was similar. The biggest reliability gap is the lack of automated tests for the agentic workflow itself — those require live API calls and are currently only covered by manual evaluation.

---

## Reflection

Building this project revealed how quickly a simple rule-based system can be transformed into something genuinely flexible by combining retrieval (iTunes) with AI reasoning (Gemini). The hardest design decision was knowing what NOT to give to the AI — keeping the scoring engine in `src/recommender.py` as tested, deterministic code rather than asking Gemini to do math it doesn't need to do.

*Note: The graded responsible-AI reflection — including how AI was used during development, one suggestion that was accepted, one that was revised, and the system's known limitations — is documented in `model_card.md` as required by Step 5 of the rubric.*
