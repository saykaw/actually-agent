"""ui/components.py — Streamlit UI components."""

import streamlit as st

VERDICT_CONFIG = {
    "settled-true":  ("✓", "Supported by evidence",   "#0d2818", "#2ea043", "#3fb950"),
    "settled-false": ("✗", "Not supported",            "#2d1117", "#f85149", "#ff7b72"),
    "contested":     ("~", "Evidence is contested",   "#2d2200", "#d29922", "#e3b341"),
    "inconclusive":  ("?", "Inconclusive",             "#0d1117", "#8b949e", "#8b949e"),
}

NODE_LEGEND = {
    "Study":          "#4C9AFF",
    "Claim":          "#FF8B00",
    "Researcher":     "#36B37E",
    "Journal":        "#998DD9",
    "Funding Source": "#FF5630",
}

EDGE_LEGEND = {
    "supports":    "#36B37E",
    "contradicts": "#FF5630",
    "funded_by":   "#FFAB00",
    "replicates":  "#4C9AFF",
    "cites":       "#8993A4",
}


def verdict_card(verdict: dict, graph: dict):
    v = verdict.get("verdict", "inconclusive")
    confidence = verdict.get("confidence", "unknown").title()
    summary = verdict.get("summary", "No summary available.")
    icon, label, bg, border, accent = VERDICT_CONFIG.get(v, VERDICT_CONFIG["inconclusive"])

    node_count = len(graph.get("nodes", []))
    edge_count = len(graph.get("edges", []))

    st.markdown(f"""
    <div style="background:{bg}; border:1px solid {border}; border-radius:10px;
                padding:24px 28px; margin-bottom:20px;">
        <div style="display:flex; align-items:flex-start; gap:16px;">
            <div style="font-size:2rem; color:{accent}; font-weight:700;
                        background:rgba(255,255,255,0.05); border-radius:8px;
                        width:48px; height:48px; display:flex; align-items:center;
                        justify-content:center; flex-shrink:0;">{icon}</div>
            <div style="flex:1;">
                <div style="font-size:1.1rem; font-weight:600; color:{accent};
                            margin-bottom:6px;">{label}</div>
                <div style="font-size:0.95rem; color:#c9d1d9; line-height:1.6;">{summary}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Confidence", confidence)
    c2.metric("Evidence nodes", node_count)
    c3.metric("Relationships", edge_count)


def legend():
    with st.expander("Legend", expanded=False):
        st.markdown("<div style='font-size:0.8rem;'>", unsafe_allow_html=True)
        st.markdown("**Nodes**")
        for label, color in NODE_LEGEND.items():
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0;">'
                f'<span style="width:10px;height:10px;border-radius:50%;background:{color};display:inline-block;"></span>'
                f'<span style="color:#c9d1d9;font-size:0.82rem;">{label}</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown("**Edges**")
        for label, color in EDGE_LEGEND.items():
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0;">'
                f'<span style="width:18px;height:2px;background:{color};display:inline-block;"></span>'
                f'<span style="color:#c9d1d9;font-size:0.82rem;">{label}</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)