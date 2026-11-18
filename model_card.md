# Model Card — AI Music Recommender

## Section 1: Limitations and Biases

**Non-deterministic output**
Gemini does not apply a fixed formula when ranking songs. Two identical inputs can produce slightly different top-5 lists across runs because the model samples from a probability distribution. This makes the system harder to test and impossible to audit with a simple expected-output check.

**Mainstream genre bias**
iTunes search relevance is uneven across genres. Mainstream genres like Pop, Hip-Hop, and R&B return dense, high-quality results. Niche or regional genres — Amapiano, Hyperpop, Afro-fusion — sometimes return zero results, forcing the system to fall back to a broader genre-only search. Users of less commercially prominent music get a weaker experience.

**Recency and popularity bias**
iTunes surfaces newer and more commercially successful songs first. Older classics or underground artists are systematically underrepresented even when they would be the best match. A user asking for "classic 70s soul" may receive recent neo-soul instead.

**English language bias**
The system was designed and tested almost entirely with English-language descriptions. While it can handle some non-English input (e.g., "musica romantica"), edge cases involving non-Latin scripts or genre names from non-English music traditions have not been evaluated.

**No personalization or memory**
The system has no concept of user history. It cannot learn from past interactions, avoid songs it has already recommended, or improve over time for a specific user.

**Gemini cannot verify song quality**
Gemini writes reasons like "this track has an infectious rhythm perfect for a party" based on its training knowledge — not by actually listening to the song. It may confidently describe a song it has incomplete knowledge of.

---

## Section 2: Potential Misuse and Prevention

**API key exposure**
If the `.env` file containing the `GEMINI_API_KEY` is accidentally committed to a public GitHub repository, anyone can use the key to make API calls at the owner's expense. Prevention: `.env` is listed in `.gitignore` so it is never tracked by git. The `.env.example` file shows the format without exposing a real key.

**Automated scraping of iTunes metadata**
The iTunes Search API is free and requires no authentication. A bad actor could modify this project to scrape Apple's music catalog at scale. Prevention: the system is designed for interactive single-user queries; no batch processing mode exists.

**Generating targeted playlists for harmful contexts**
A user could describe a harmful mood or activity in their input (e.g., promoting self-harm). Gemini has built-in content safety filters that would refuse or redirect such requests, but no additional application-level guardrail exists for this. For a production system, an input screening step would be appropriate.

---

## Section 3: What Surprised Me While Testing

**The model deprecation mid-project**
`gemini-2.0-flash` was deprecated while the project was being built and had to be replaced with `gemini-3.8-flash`. This was unexpected and highlighted how quickly AI infrastructure can change — a system built against a specific model can break without any change to the application code itself.

**Conflicting keywords surface genre over mood**
When the input was `"heavy metal relaxing ambient"`, the system returned metal songs rather than ambient ones. Gemini treated genre as the dominant signal and largely ignored the mood/energy contradiction. This mirrored the exact bias documented in the original project's scoring algorithm — genre dominates regardless of whether the ranker is mathematical or AI-based.

**Merging API calls had a larger speed impact than expected**
Reducing from four sequential Gemini calls to two cut response time roughly in half. The bottleneck was not the size of the prompts but the round-trip latency of each API call. This was a bigger win than any prompt optimization.

**iTunes returns nothing for some valid genres**
Searches for terms like `"lofi study beats"` occasionally returned zero results despite lofi being a popular genre on iTunes. The issue was search term phrasing, not catalog availability. The fallback to a genre-only retry resolved this, but it revealed that the quality of the iTunes query matters as much as the quality of the Gemini profile.

**JSON parsing edge cases were real**
Gemini does not always return a clean JSON string. During testing it sometimes wrapped the JSON in a ```json code block, sometimes added an introductory sentence, and once returned the JSON with trailing commentary. The `_extract_json()` function and its six automated tests were directly motivated by these real failures.

---

## Section 4: AI Collaboration

This project was built in collaboration with Claude (Anthropic). The following documents one suggestion that was accepted as proposed and one that was revised.

**Suggestion accepted: Agentic RAG with iTunes Search API**

When asked what advanced feature to add, Claude suggested replacing the fixed 18-song CSV catalog with Apple's iTunes Search API and using Gemini as a ranking layer — making the system a Retrieval-Augmented Generation (RAG) pipeline. This suggestion was accepted as proposed because it solved the core limitation of the original project (a closed, static catalog) and introduced two rubric requirements at once: RAG and agentic workflow. The result is a system that works for any genre from any country rather than a hardcoded list of 18 songs.

**Suggestion changed: the local CSV toggle**

Claude's initial implementation included a toggle in the Streamlit UI offering two modes: "Local catalog (18 songs)" and "Search real songs online." This was rejected and replaced with a single worldwide iTunes-only mode. The reason was not that the toggle was wrong — it worked — but that it was over-engineered for this project. Maintaining two separate code paths (CSV scoring + iTunes RAG) doubled the complexity without adding meaningful value since the original CSV catalog was always going to be inferior to a live worldwide search. Scoping down to a single mode made the codebase cleaner, the UI simpler, and the architecture easier to explain. This is documented in the system design as a deliberate trade-off.
