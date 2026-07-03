"""
actually_agent/agent.py — ADK Agent definition.

ADK requires a file named agent.py with a root_agent variable.
This is where the agent's instructions, model, and tools are defined.

The agent is called programmatically from runner.py — not via adk web.
adk web can be used during development for quick testing.
"""

import sys
import os
from pathlib import Path

# Make sibling packages importable when running via ADK
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm  # ADD THIS
from mcp.pubmed_server import PUBMED_TOOLS
from mcp.semantic_scholar_server import SEMANTIC_TOOLS
from actually_agent.tools import make_submit_finding, get_graph_store
from actually_agent.prompts import build_instruction

# Build the full instruction by loading the SKILL.md
instruction = build_instruction()

# All tools the agent can use:
# - 3 PubMed tools (search, get paper, check retraction)
# - 3 Semantic Scholar tools (search, get citations, get paper)
# - submit_finding (builds the knowledge graph)
submit_finding = make_submit_finding(get_graph_store())

root_agent = Agent(
    name="actually_agent",
    model="gemini-2.5-flash-lite",
    description=(
        "A rigorous scientific claim investigator. "
        "Traces original studies, audits methodology, hunts for contradictions, "
        "checks replication, and renders an evidence knowledge graph."
    ),
    instruction=instruction,
    tools=PUBMED_TOOLS + SEMANTIC_TOOLS + [submit_finding],
)