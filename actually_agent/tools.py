"""
actually_agent/tools.py — Custom tools for the ADK agent.

PubMed and Semantic Scholar tools live in mcp/.
This file only defines submit_finding, which builds the knowledge graph.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security import sanitise_tool_output
from actually_agent.graph_store import get_graph_store, GraphStore


def make_submit_finding(graph_store: GraphStore):
    """Return a submit_finding function bound to the given GraphStore."""

    def submit_finding(
        node_id: str,
        node_type: str,
        node_label: str,
        edge_from: str = "",
        edge_to: str = "",
        edge_relation: str = "",
        notes: str = "",
    ) -> dict:
        """
        Log a discovered entity and optionally its relationship to another entity.

        node_type: study | claim | researcher | journal | funding_source
        edge_relation: supports | contradicts | funded_by | replicates | cites

        Call this for every study, researcher, journal, and funding source found.
        This builds the knowledge graph shown to the user at the end.

        Returns a confirmation dict.
        """
        safe_notes = sanitise_tool_output(notes, source="submit_finding")
        graph_store.add_node(
            id=node_id,
            type=node_type,
            label=node_label,
            notes=safe_notes,
        )
        if edge_from and edge_to and edge_relation:
            graph_store.add_edge(
                from_id=edge_from,
                to_id=edge_to,
                relation=edge_relation,
            )
        return {"status": "logged", "node": node_label, "type": node_type}

    return submit_finding