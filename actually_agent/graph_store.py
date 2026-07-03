"""
actually_agent/graph_store.py — Shared graph state.

The ADK agent calls submit_finding() during investigation.
Each call accumulates nodes and edges here.
This module holds the global store that runner.py reads after the agent finishes.
"""

from dataclasses import dataclass, field


@dataclass
class GraphStore:
    nodes: list[dict] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)

    def add_node(self, id: str, type: str, label: str, notes: str = ""):
        if not any(n["id"] == id for n in self.nodes):
            self.nodes.append({"id": id, "type": type, "label": label, "notes": notes})

    def add_edge(self, from_id: str, to_id: str, relation: str):
        self.edges.append({"from": from_id, "to": to_id, "relation": relation})

    def to_dict(self) -> dict:
        return {"nodes": self.nodes, "edges": self.edges}

    def reset(self):
        self.nodes.clear()
        self.edges.clear()

    def is_empty(self) -> bool:
        return len(self.nodes) == 0


# Module-level singleton — shared between agent.py and runner.py
_store = GraphStore()


def get_graph_store() -> GraphStore:
    return _store


def reset_graph_store():
    _store.reset()