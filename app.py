"""
app.py — Streamlit entry point.
Run with: python -m streamlit run app.py
"""

import streamlit as st
import streamlit.components.v1 as components

from runner import investigate_claim
from ui import render_graph
        
st.set_page_config(
    page_title="Actually?",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# MOCK MODE — remove when API is available
# import json
# with open("mock_result.json") as f:
#     if "result" not in st.session_state:
#         st.session_state["result"] = json.load(f)
 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=DM+Mono:wght@400;500&display=swap');
 
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"], .stApp {
    font-family: 'DM Sans', sans-serif !important;
    background-color: #FAFAF8 !important;
    color: #111827 !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 3.5rem 5rem 5rem 5rem !important; max-width: 1080px !important; }
 
.stTextInput > div > div > input {
    background: #FFFFFF !important; border: 1.5px solid #D1D5DB !important;
    border-radius: 8px !important; color: #111827 !important;
    font-size: 1rem !important; padding: 12px 16px !important; height: 46px !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: #1A56DB !important; box-shadow: 0 0 0 3px rgba(26,86,219,0.08) !important;
}
.stTextInput > div > div > input::placeholder { color: #B0B8C4 !important; }
.stTextInput label { display: none !important; }
 
.stButton > button {
    background: #111827 !important; color: #FFFFFF !important; border: none !important;
    border-radius: 8px !important; padding: 0 28px !important; font-weight: 600 !important;
    font-size: 0.95rem !important; height: 46px !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stButton > button:hover { background: #1F2937 !important; }
 
[data-testid="metric-container"] {
    background: #FFFFFF !important; border: 1px solid #E5E7EB !important;
    border-radius: 8px !important; padding: 16px 20px !important;
}
[data-testid="metric-container"] * { color: #111827 !important; font-family: 'DM Sans', sans-serif !important; }
[data-testid="metric-container"] label {
    font-size: 0.78rem !important; font-weight: 600 !important;
    text-transform: uppercase !important; letter-spacing: 0.08em !important;
    color: #6B7280 !important;
}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
    font-size: 1.6rem !important; font-weight: 700 !important; color: #111827 !important;
}
 
hr { border-color: #EDEDED !important; margin: 2.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)
 
# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:2.5rem;">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
        <span style="font-size:2.2rem;line-height:1;">🔬</span>
        <span style="font-size:2.6rem;font-weight:700;color:#111827;
                     letter-spacing:-0.04em;font-family:'DM Sans',sans-serif;line-height:1.1;">
            Actually?
        </span>
    </div>
    <p style="color:#6B7280;font-size:1.05rem;margin:0;max-width:500px;
              line-height:1.65;font-family:'DM Sans',sans-serif;">
        Claim it. Unclaim it. Repeat until the evidence agrees.
    </p>
</div>
""", unsafe_allow_html=True)
 
# ── Search ────────────────────────────────────────────────────────────────────
col_in, col_btn = st.columns([5, 1])
with col_in:
    claim = st.text_input(
        "claim", label_visibility="collapsed",
        placeholder='Try: "Sugar causes hyperactivity in children"',
        max_chars=300,
    )
with col_btn:
    run = st.button("Investigate →", type="primary", use_container_width=True)
 
# ── Run ───────────────────────────────────────────────────────────────────────
if run and claim:
    st.session_state.pop("result", None)
    st.session_state.pop("error", None)
    with st.spinner("Searching PubMed, OpenAlex, checking citations..."):
        result = investigate_claim(claim)
    if result.get("error"):
        st.session_state["error"] = result["error"]
    else:
        st.session_state["result"] = result
 
# ── Error ─────────────────────────────────────────────────────────────────────
if st.session_state.get("error"):
    st.markdown(f"""
    <div style="border-left:4px solid #DC2626;padding:14px 18px;background:#FEF2F2;
                border-radius:0 8px 8px 0;margin-top:1.5rem;color:#991B1B;
                font-size:0.95rem;font-family:'DM Sans',sans-serif;line-height:1.6;">
        {st.session_state["error"]}
    </div>
    """, unsafe_allow_html=True)
 
# ── Results ───────────────────────────────────────────────────────────────────
result = st.session_state.get("result")
 
if result:
    verdict    = result.get("verdict", {})
    graph_data = result.get("graph", {"nodes": [], "edges": []})
    v          = verdict.get("verdict", "inconclusive")
    confidence = verdict.get("confidence", "unknown").title()
    summary    = verdict.get("summary", "No summary available.")
    conclusion = result.get("conclusion_text", "")
    last_brace = conclusion.rfind("{")
    display_conclusion = conclusion[:last_brace].strip() if last_brace > 0 else conclusion
 
    VERDICT_CONFIG = {
        "settled-true":  ("#16A34A", "Supported by evidence",  "#F0FDF4", "✓"),
        "settled-false": ("#DC2626", "Not supported",           "#FEF2F2", "✗"),
        "contested":     ("#D97706", "Evidence is contested",  "#FFFBEB", "~"),
        "inconclusive":  ("#6B7280", "Inconclusive",            "#F9FAFB", "?"),
    }
    accent, label, bg, icon = VERDICT_CONFIG.get(v, VERDICT_CONFIG["inconclusive"])
 
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
 
    # ── Verdict card ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="border-left:5px solid {accent};background:{bg};
                border-radius:0 10px 10px 0;padding:24px 28px;margin-bottom:28px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <span style="font-size:1.4rem;font-weight:700;color:{accent};
                         font-family:'DM Mono',monospace;">{icon}</span>
            <span style="font-size:1.25rem;font-weight:700;color:{accent};
                         font-family:'DM Sans',sans-serif;letter-spacing:-0.01em;">{label}</span>
        </div>
        <p style="margin:0;color:#374151;font-size:1rem;line-height:1.75;
                  font-family:'DM Sans',sans-serif;max-width:680px;">{summary}</p>
    </div>
    """, unsafe_allow_html=True)
 
    # ── Metrics ───────────────────────────────────────────────────────────────
    node_count = len(graph_data.get("nodes", []))
    edge_count = len(graph_data.get("edges", []))

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:8px;">
        <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:8px;padding:18px 22px;">
            <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.1em;color:#6B7280;margin-bottom:6px;
                        font-family:'DM Sans',sans-serif;">Confidence</div>
            <div style="font-size:1.6rem;font-weight:700;color:#111827;
                        font-family:'DM Sans',sans-serif;">{confidence}</div>
        </div>
        <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:8px;padding:18px 22px;">
            <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.1em;color:#6B7280;margin-bottom:6px;
                        font-family:'DM Sans',sans-serif;">Evidence Nodes</div>
            <div style="font-size:1.6rem;font-weight:700;color:#111827;
                        font-family:'DM Sans',sans-serif;">{node_count}</div>
        </div>
        <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:8px;padding:18px 22px;">
            <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.1em;color:#6B7280;margin-bottom:6px;
                        font-family:'DM Sans',sans-serif;">Relationships</div>
            <div style="font-size:1.6rem;font-weight:700;color:#111827;
                        font-family:'DM Sans',sans-serif;">{edge_count}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
 
    # ── Evidence map ──────────────────────────────────────────────────────────
    NODE_LEGEND = {
        "Study": "#3B82F6", "Claim": "#F59E0B", "Researcher": "#10B981",
        "Journal": "#8B5CF6", "Funding Source": "#EF4444",
    }
    EDGE_LEGEND = {
        "supports": "#16A34A", "contradicts": "#DC2626",
        "funded_by": "#D97706", "replicates": "#3B82F6", "cites": "#9CA3AF",
    }
 
    st.markdown("""
    <p style="font-size:0.98rem;font-weight:700;text-transform:uppercase;
              letter-spacing:0.12em;color:#111827;margin-bottom:14px;
              font-family:'DM Sans',sans-serif;">Evidence Map</p>
    """, unsafe_allow_html=True)
 
    legend_parts = []
    for lbl, col in NODE_LEGEND.items():
        legend_parts.append(
            f'<div style="display:flex;align-items:center;gap:6px;">'
            f'<span style="width:10px;height:10px;border-radius:50%;background:{col};'
            f'flex-shrink:0;display:inline-block;"></span>'
            f'<span style="font-size:0.85rem;color:#4B5563;font-family:DM Sans,sans-serif;">'
            f'{lbl}</span></div>'
        )
    for lbl, col in EDGE_LEGEND.items():
        legend_parts.append(
            f'<div style="display:flex;align-items:center;gap:6px;">'
            f'<span style="width:18px;height:2px;background:{col};'
            f'flex-shrink:0;display:inline-block;border-radius:2px;"></span>'
            f'<span style="font-size:0.85rem;color:#4B5563;font-family:DM Sans,sans-serif;">'
            f'{lbl}</span></div>'
        )
 
    st.markdown(
        '<div style="display:flex;flex-wrap:wrap;gap:18px;margin-bottom:16px;">'
        + "".join(legend_parts) + "</div>",
        unsafe_allow_html=True,
    )
 
    if graph_data["nodes"]:
        html = render_graph(graph_data)
        components.html(html, height=580)
    else:
        st.markdown("""
        <div style="border:1.5px dashed #D1D5DB;border-radius:10px;padding:56px;
                    text-align:center;color:#9CA3AF;font-size:0.95rem;
                    font-family:'DM Sans',sans-serif;background:#FFFFFF;">
            No evidence nodes were logged for this claim.
        </div>
        """, unsafe_allow_html=True)
 
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

    # ── Full analysis ─────────────────────────────────────────────────────────
    st.markdown("""
    <p style="font-size:0.98rem;font-weight:700;text-transform:uppercase;
              letter-spacing:0.12em;color:#111827;margin-bottom:14px;
              font-family:'DM Sans',sans-serif;">Full Analysis</p>
    """, unsafe_allow_html=True)
 
    if display_conclusion:
        st.markdown(f"""
        <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;
                    padding:28px 32px;color:#374151;line-height:1.9;font-size:1rem;
                    font-family:'DM Sans',sans-serif;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            {display_conclusion}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;
                    padding:28px 32px;color:#9CA3AF;font-size:0.95rem;
                    font-family:'DM Sans',sans-serif;">
            No written conclusion was generated.
        </div>
        """, unsafe_allow_html=True)
 