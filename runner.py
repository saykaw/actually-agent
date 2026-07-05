"""
runner.py — Programmatic ADK runner.

Runs the ADK agent in a dedicated thread with its own event loop,
completely isolated from Streamlit's internal event loop.
Graph store is instantiated fresh per investigation and passed explicitly
— no global singleton, no shared state bugs across threads.
"""

import asyncio
import json
import os
import threading
from typing import Callable

from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

from security import sanitise_claim, InputValidationError
from actually_agent.graph_store import GraphStore
from actually_agent.tools import make_submit_finding
from actually_agent.prompts import build_instruction
from mcp import ALL_MCP_TOOLS
from actually_agent.graph_store import GraphStore, get_graph_store, reset_graph_store


load_dotenv()

if not os.environ.get("GOOGLE_API_KEY") and os.environ.get("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
    
print(os.environ["GOOGLE_API_KEY"])

APP_NAME = "actually_agent"


def _extract_trailing_json(text: str) -> dict:
    start = text.rfind("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        return json.loads(text[start: end + 1])
    except json.JSONDecodeError:
        return {}


def _build_fresh_agent(graph_store: GraphStore):
    """Build a fresh ADK agent bound to a specific graph store instance."""
    from google.adk.agents import Agent

    model_name = os.environ.get("ACTUALLY_MODEL")
    model = model_name

    reset_graph_store()
    submit_finding = make_submit_finding(get_graph_store())
    
    return Agent(
        name="actually_agent",
        model=model,
        description=(
            "A rigorous scientific claim investigator. "
            "Traces original studies, audits methodology, hunts for contradictions, "
            "checks replication, and renders an evidence knowledge graph."
        ),
        instruction=build_instruction(),
        tools=ALL_MCP_TOOLS + [submit_finding],
    )


async def _run_agent(claim: str, graph_store: GraphStore) -> dict:
    """Async core — runs inside a dedicated thread's event loop."""
    agent = _build_fresh_agent(graph_store)
    runner = InMemoryRunner(agent=agent, app_name=APP_NAME)

    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id="user",
        state={},
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=(
            f'Investigate this scientific claim: "{claim}"\n\n'
            f"Start with the claim-deconstructor skill. Then use PubMed and "
            f"Semantic Scholar to investigate. Call submit_finding for every "
            f"entity you discover. End with a verdict JSON."
        ))],
    )

    full_response_text = ""
    
    async for event in runner.run_async(
    user_id="user",
    session_id=session.id,
    new_message=user_message,
    ):  
        error_code = getattr(event, "error_code", None)
        error_message = getattr(event, "error_message", None)
        if error_code or error_message:
            print(f"[EVENT ERROR] code={error_code} message={error_message}")

        if hasattr(event, "content") and event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    full_response_text += part.text
                elif hasattr(part, "function_call") and part.function_call:
                    print(f"[tool call: {part.function_call.name}] args: {dict(part.function_call.args)}")
                elif hasattr(part, "function_response") and part.function_response:
                    print(f"[tool response: {part.function_response.name}] result: {str(part.function_response.response)[:200]}")
        else:
            print(f"[EMPTY EVENT] {event}")

    verdict = _extract_trailing_json(full_response_text)
    graph = get_graph_store().to_dict()


    print(f"\nDone. Graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

    return {
        "claim": claim,
        "conclusion_text": full_response_text,
        "verdict": verdict,
        "graph": graph,
    }


def investigate_claim(
    claim: str,
    log_callback: Callable[[str], None] | None = None,
) -> dict:
    """
    Public API called by app.py.
    Runs the ADK agent in a dedicated thread with its own event loop.
    Graph store is fresh per call — no shared state issues.
    """
    try:
        claim = sanitise_claim(claim)
    except InputValidationError as e:
        return {
            "claim": claim,
            "error": str(e),
            "conclusion_text": "",
            "verdict": {},
            "graph": {"nodes": [], "edges": []},
        }

    # Fresh graph store per investigation — no global singleton
    graph_store = GraphStore()
    result_container = {}

    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result_container["result"] = loop.run_until_complete(
                _run_agent(claim, graph_store)
            )
        except Exception as e:
            print(f"Agent error: {e}")
            result_container["result"] = {
                "claim": claim,
                "error": str(e),
                "conclusion_text": "",
                "verdict": {},
                "graph": {"nodes": [], "edges": []},
            }
        finally:
            loop.close()

    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    thread.join()

    return result_container.get("result", {
        "claim": claim,
        "error": "Investigation returned no result.",
        "conclusion_text": "",
        "verdict": {},
        "graph": {"nodes": [], "edges": []},
    })


if __name__ == "__main__":
    claim = input("Enter a claim: ").strip() or "smoking causes lung cancer"
    result = investigate_claim(claim)
    print("\n=== VERDICT ===")
    print(json.dumps(result["verdict"], indent=2))
    print(f"Graph: {len(result['graph']['nodes'])} nodes, {len(result['graph']['edges'])} edges")