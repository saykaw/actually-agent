"""ui/graph_renderer.py — PyVis rendering, light mode."""

from pyvis.network import Network

NODE_COLORS = {
    "study":          "#3B82F6",
    "claim":          "#F59E0B",
    "researcher":     "#10B981",
    "journal":        "#8B5CF6",
    "funding_source": "#EF4444",
}

EDGE_COLORS = {
    "supports":    "#16A34A",
    "contradicts": "#DC2626",
    "funded_by":   "#D97706",
    "replicates":  "#3B82F6",
    "cites":       "#9CA3AF",
}

OPTIONS = """
{
  "physics": {
    "stabilization": {"iterations": 200},
    "barnesHut": {
      "gravitationalConstant": -6000,
      "springLength": 180,
      "springConstant": 0.04
    }
  },
  "edges": {
    "font": {"size": 10, "color": "#6B7280", "strokeWidth": 0},
    "smooth": {"type": "curvedCW", "roundness": 0.15},
    "arrows": {"to": {"enabled": true, "scaleFactor": 0.6}},
    "width": 1.5
  },
  "nodes": {
    "font": {"size": 13, "color": "#111827", "bold": false},
    "borderWidth": 0,
    "shadow": {"enabled": true, "color": "rgba(0,0,0,0.08)", "size": 6, "x": 0, "y": 2}
  },
  "interaction": {
    "hover": true,
    "tooltipDelay": 100
  }
}
"""


def render_graph(graph_data: dict, height: str = "560px") -> str:
    net = Network(
        height=height,
        width="100%",
        bgcolor="#FFFFFF",
        font_color="#111827",
        directed=True,
    )

    for node in graph_data.get("nodes", []):
        color = NODE_COLORS.get(node.get("type", ""), "#9CA3AF")
        net.add_node(
            node["id"],
            label=node.get("label", node["id"]),
            title=f"<div style='font-family:DM Sans,sans-serif;font-size:12px;max-width:240px;'>{node.get('notes', '')}</div>" if node.get("notes") else "",
            color={"background": color, "border": color,
                   "highlight": {"background": color, "border": color}},
            size=20,
        )

    for edge in graph_data.get("edges", []):
        relation = edge.get("relation", "")
        color = EDGE_COLORS.get(relation, "#9CA3AF")
        net.add_edge(
            edge["from"],
            edge["to"],
            label=relation,
            color={"color": color, "highlight": color},
        )

    net.set_options(OPTIONS)

    # Inject light mode CSS into the generated HTML
    html = net.generate_html()
    html = html.replace(
        "<body>",
        "<body style='background:#FFFFFF; margin:0; padding:0;'>"
    )
    return html