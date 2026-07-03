# Actually? 🔬

A scientific claim investigator powered by Google ADK.

Paste any scientific claim. The ADK agent traces the original study via PubMed,
checks for retractions, hunts for contradicting evidence via Semantic Scholar's
citation graph, and renders everything as an interactive knowledge map plus a
synthesized verdict.

---

## Architecture

```
actually-agent/
├── actually_agent/         # ADK agent package (must be named to match root_agent)
│   ├── agent.py            # root_agent definition — ADK entry point
│   ├── prompts.py          # loads SKILL.md into agent instruction
│   ├── tools.py            # submit_finding tool (builds the knowledge graph)
│   ├── graph_store.py      # shared graph state accumulator
│   └── __init__.py
├── skills/
│   └── claim-deconstructor/
│       └── SKILL.md        # the investigation skill loaded at runtime
├── mcp/
│   ├── pubmed_server.py         # PubMed MCP (3 tools)
│   └── semantic_scholar_server.py # Semantic Scholar MCP (3 tools)
├── security/
│   └── checks.py           # input sanitisation + prompt injection defence
├── ui/
│   ├── graph_renderer.py   # PyVis knowledge graph
│   └── components.py       # verdict card, legend
├── runner.py               # programmatic ADK runner (called by app.py)
└── app.py                  # Streamlit entry point
```

## Key concepts demonstrated

| Concept          | Implementation                                                           |
| ---------------- | ------------------------------------------------------------------------ |
| **Agent / ADK**  | `actually_agent/agent.py` — ADK `Agent` with 7 tools                     |
| **Agent skills** | `skills/claim-deconstructor/SKILL.md` loaded into instruction at runtime |
| **MCP servers**  | PubMed MCP + Semantic Scholar MCP in `mcp/`                              |
| **Security**     | Input sanitisation + prompt injection defence in `security/`             |
| **Antigravity**  | Installed via `google-adk[antigravity]`                                  |

---

## Setup

```bash
# 1. Clone and create venv
git clone https://github.com/your-username/actually-agent.git
cd actually-agent
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1

# 2. Install (includes ADK + Antigravity)
pip install -r requirements.txt

# 3. Set up API key
cp .env.example .env
# Add your Gemini key from https://aistudio.google.com/apikey
# Set both GOOGLE_API_KEY and GEMINI_API_KEY to the same value

# 4. Test MCP servers (no API key needed — both are free public APIs)
python mcp/pubmed_server.py
python mcp/semantic_scholar_server.py

# 5. Test the agent loop directly
python runner.py

# 6. Run the full app
streamlit run app.py
```

## Development testing with ADK web UI

During development you can also use ADK's built-in web UI to test the agent:

```bash
# Run from the project root (parent of actually_agent/)
adk web .
# Then open http://localhost:8000
```

This is useful for debugging tool calls and seeing the full event stream.
Your Streamlit app (app.py) is the real UI for the demo and submission.

## Tuning

- **Agent behaviour** → `skills/claim-deconstructor/SKILL.md` + `actually_agent/prompts.py`
- **Graph not building** → agent isn't calling submit_finding enough; tighten the instruction
- **Graph visuals** → `ui/graph_renderer.py`
- **Security rules** → `security/checks.py`
