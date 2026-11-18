# Reproducible Execution Evidence

## Automated Test Run

Command:
```
pytest tests/ -v
```

Output:
```
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\yodah\applied-ai-system-project
plugins: anyio-4.16.0
collecting ... collected 13 items

tests/test_core.py::test_extract_json_clean_string PASSED                [  7%]
tests/test_core.py::test_extract_json_wrapped_in_code_block PASSED       [ 15%]
tests/test_core.py::test_extract_json_embedded_in_prose PASSED           [ 23%]
tests/test_core.py::test_extract_json_parses_array PASSED                [ 30%]
tests/test_core.py::test_extract_json_raises_on_garbage_input PASSED     [ 38%]
tests/test_core.py::test_extract_json_handles_extra_whitespace PASSED    [ 46%]
tests/test_core.py::test_get_client_raises_without_api_key PASSED        [ 53%]
tests/test_core.py::test_parse_itunes_returns_songs PASSED               [ 61%]
tests/test_core.py::test_parse_itunes_filters_out_non_songs PASSED       [ 69%]
tests/test_core.py::test_parse_itunes_upgrades_artwork_resolution PASSED [ 76%]
tests/test_core.py::test_parse_itunes_handles_missing_fields_gracefully PASSED [ 84%]
tests/test_core.py::test_parse_itunes_empty_list_returns_empty PASSED    [ 92%]
tests/test_core.py::test_parse_itunes_no_artwork_upgrade_when_blank PASSED [100%]

============================= 13 passed in 1.08s ==============================
```

---

## Sample Agent Log

Captured from `logs/agent_20261118.log` during a live run:

```
2026-11-18 00:41:22 | INFO | src.agent | Agent started | input='afrobeats party'
2026-11-18 00:41:24 | INFO | src.agent | Profile + query | genre=Afrobeats | query='afrobeats dance party'
2026-11-18 00:41:24 | INFO | src.itunes | iTunes search | query='afrobeats dance party' limit=30
2026-11-18 00:41:24 | INFO | src.itunes | iTunes returned 28 songs
2026-11-18 00:41:26 | INFO | src.agent | Agent done | top='Ke Star' by Focalistic
```

---

## Startup Guardrail — Missing API Key

Command (run without a `.env` file):
```
streamlit run app.py
```

UI shows:
```
GEMINI_API_KEY not found.

Create a .env file in the project root:
  GEMINI_API_KEY=your_key_here
```
App halts — no API calls are made.
