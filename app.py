"""
AI Music Recommender — Streamlit UI
Searches Apple's worldwide iTunes catalog using an agentic RAG workflow.

Run:
    streamlit run app.py
"""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.agent import get_client, extract_profile_and_query, rank_and_summarize
from src.itunes import search_songs
from src.logger import setup_logger

load_dotenv()
setup_logger()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Music Recommender",
    page_icon="🎵",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS — dark music theme
# ---------------------------------------------------------------------------

st.markdown("""
<style>
/* Card container */
div[data-testid="column"] > div {
    background: #1a1a2e;
    border-radius: 12px;
    padding: 12px;
    border: 1px solid #2d2d4e;
    transition: border-color 0.2s;
}
div[data-testid="column"] > div:hover {
    border-color: #a855f7;
}

/* Song title bold */
div[data-testid="column"] strong {
    color: #e2e8f0;
    font-size: 0.95rem;
}

/* Artist italic */
div[data-testid="column"] em {
    color: #a855f7;
}

/* Apple Music link */
div[data-testid="column"] a {
    color: #a855f7 !important;
    font-size: 0.8rem;
    text-decoration: none;
}
div[data-testid="column"] a:hover {
    text-decoration: underline;
}

/* Blockquote (reason) */
blockquote {
    border-left: 3px solid #a855f7 !important;
    padding-left: 8px !important;
    color: #94a3b8 !important;
    font-size: 0.82rem !important;
    margin: 4px 0 !important;
}

/* Input box */
div[data-baseweb="input"] {
    border-color: #2d2d4e !important;
}

/* Divider */
hr {
    border-color: #2d2d4e !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

ASSETS = Path(__file__).parent / "assets"
banner_path = ASSETS / "banner.png"
no_artwork_path = ASSETS / "no_artwork.png"

if banner_path.exists():
    st.image(str(banner_path), use_container_width=True)
else:
    st.title("🎵 AI Music Recommender")

st.caption(
    "Describe what you're in the mood for — the agent searches Apple's worldwide "
    "catalog and finds the best matches using Gemini AI."
)

# ---------------------------------------------------------------------------
# API key guard
# ---------------------------------------------------------------------------

if not os.getenv("GEMINI_API_KEY"):
    st.error(
        "**GEMINI_API_KEY not found.**\n\n"
        "Create a `.env` file in the project root:\n"
        "```\nGEMINI_API_KEY=your_key_here\n```"
    )
    st.stop()

# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

user_input = st.text_input(
    "What kind of music do you want?",
    placeholder="e.g. upbeat Afrobeats for a party, sad piano for a rainy day, K-pop workout songs...",
)

col_btn, col_note = st.columns([1, 4])
with col_btn:
    run_btn = st.button("Get Recommendations", type="primary")
with col_note:
    st.caption("Powered by Gemini AI · Sourced from iTunes worldwide catalog")

# ---------------------------------------------------------------------------
# Run agent with live step-by-step progress
# ---------------------------------------------------------------------------

if run_btn and user_input.strip():

    profile = None
    query = None
    candidates = []
    ranked = []
    summary = ""
    steps = []
    error = None

    with st.status("Working on your recommendations...", expanded=True) as status:
        try:
            client = get_client()

            # Step 1 — profile + query (Gemini call 1)
            status.write("🎯 Understanding what you're looking for...")
            profile, query = extract_profile_and_query(client, user_input.strip())
            status.write(
                f"✅ Profile: **{profile['genre']}** · **{profile['mood']}** · "
                f"energy **{profile['target_energy']:.2f}**"
            )
            steps.append(("Extract Profile & Query", user_input, (
                f"genre={profile['genre']}, mood={profile['mood']}, "
                f"energy={profile['target_energy']:.2f} | query=\"{query}\""
            )))

            # Step 2 — iTunes search
            status.write(f"🔍 Searching iTunes for **\"{query}\"**...")
            candidates = search_songs(query, limit=30)

            if not candidates:
                fallback = profile["genre"]
                status.write(f"↩️ No results — retrying with **\"{fallback}\"**...")
                candidates = search_songs(fallback, limit=30)
                steps.append(("iTunes Search (fallback)", f"'{query}' had 0 results",
                               f"Retried '{fallback}' → {len(candidates)} songs"))
            else:
                steps.append(("iTunes Search", f"query=\"{query}\"",
                               f"Retrieved {len(candidates)} songs from Apple's worldwide catalog"))

            if not candidates:
                raise RuntimeError(
                    "iTunes returned no results. Check your connection or try a different description."
                )

            status.write(f"✅ Found **{len(candidates)} songs** from Apple's worldwide catalog")

            # Step 3 — rank + summarize (Gemini call 2)
            status.write("🤖 AI is ranking songs and writing your summary...")
            ranked, summary = rank_and_summarize(client, user_input.strip(), profile, candidates)
            steps.append(("Rank & Summarize", f"{len(candidates)} candidates",
                           f"Top: \"{ranked[0]['title']}\" by {ranked[0]['artist']}"))

            status.update(label="Done! Here are your picks.", state="complete", expanded=False)

        except ValueError as e:
            error = str(e)
            status.update(label="Failed.", state="error", expanded=False)
        except RuntimeError as e:
            error = str(e)
            status.update(label="Failed.", state="error", expanded=False)
        except Exception as e:
            error = f"Unexpected error: {e}"
            status.update(label="Failed.", state="error", expanded=False)

    if error:
        st.error(error)
        st.stop()

    # --- AI summary ---
    st.success(summary)

    # --- Profile pill ---
    p = profile
    st.info(
        f"Profile → genre: **{p['genre']}** | mood: **{p['mood']}** | "
        f"energy: **{p['target_energy']:.2f}** · iTunes query: **\"{query}\"**"
    )

    # --- Recommendation cards ---
    st.subheader("Top Picks")
    cols = st.columns(5)
    for song, col in zip(ranked, cols):
        with col:
            artwork = song.get("artwork_url")
            if artwork:
                st.image(artwork, use_container_width=True)
            elif no_artwork_path.exists():
                st.image(str(no_artwork_path), use_container_width=True)
            else:
                st.markdown("🎵")

            st.markdown(f"**{song['title']}**")
            st.markdown(f"*{song['artist']}*")
            st.caption(song["genre"])
            if song.get("album"):
                st.caption(f"📀 {song['album']}")

            st.markdown(f"> {song['reason']}")

            if song.get("preview_url"):
                st.audio(song["preview_url"], format="audio/mp4")

            if song.get("track_url"):
                st.markdown(f"[Open in Apple Music ↗]({song['track_url']})")

    # --- Agent step trace ---
    st.divider()
    with st.expander("How the agent found these", expanded=False):
        for name, inp, out in steps:
            st.markdown(f"**{name}**")
            st.markdown(f"- *In:* {inp}")
            st.markdown(f"- *Out:* {out}")
            st.divider()

elif run_btn and not user_input.strip():
    st.warning("Please describe what you're looking for first.")
