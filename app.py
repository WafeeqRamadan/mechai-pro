# -*- coding: utf-8 -*-
"""
MechAI Pro v20 — Clean Internal Knowledge-Only Build
No OpenAI, no Gemini, no external AI provider UI.
Primary reference brain: bundled knowledge_packs.
Run: streamlit run app.py
"""
from __future__ import annotations

import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple

import streamlit as st

BUILD_ID = "V20_INTERNAL_ONLY_CLEAN_REPO_2026_06_11"
APP_DIR = Path(__file__).parent
KNOWLEDGE_DIR = APP_DIR / "knowledge_packs"

WORKSPACES = {
    "chief": "🧠 General engineering",
    "mechanical": "🔧 Product R&D / Design",
    "solidworks": "🧩 CAD / SolidWorks",
    "fea": "📊 Simulation / FEA",
    "cfd": "🌊 CFD / Thermal",
    "manufacturing": "🏭 Manufacturing / DFM",
    "materials": "🧪 Materials selection",
    "patent": "💡 Innovation / Patent",
}

WORKSPACE_TO_PACK = {
    "chief": "",
    "mechanical": "mechanical_design",
    "solidworks": "cad_solidworks",
    "fea": "simulation_fea",
    "cfd": "cfd_thermal",
    "manufacturing": "manufacturing_dfm",
    "materials": "materials_selection",
    "patent": "innovation_patent",
}

PACK_TITLES = {
    "mechanical_design": "Mechanical Design",
    "cad_solidworks": "CAD / SolidWorks",
    "simulation_fea": "Simulation / FEA",
    "cfd_thermal": "CFD / Thermal",
    "manufacturing_dfm": "Manufacturing / DFM",
    "materials_selection": "Materials Selection",
    "innovation_patent": "Innovation / Patent",
}

INTENT_KEYWORDS = {
    "mechanical": ["design", "shaft", "bearing", "spring", "gear", "stress", "fatigue", "load", "safety factor", "tolerance", "gd&t", "mechanism", "bracket", "housing"],
    "solidworks": ["solidworks", "macro", "vba", "api", "part", "assembly", "drawing", "bom", "step", "dxf", "sketch", "feature", "extrude", "cad"],
    "fea": ["fea", "simulation", "ansys", "static", "modal", "buckling", "mesh", "boundary", "contact", "convergence", "finite element"],
    "cfd": ["cfd", "fluent", "flow", "thermal", "heat", "pressure drop", "reynolds", "turbulence", "y+", "convection", "fluid", "pipe"],
    "manufacturing": ["dfm", "dfa", "manufacturing", "injection", "molding", "moulding", "machining", "sheet metal", "tooling", "cycle time", "scrap", "assembly", "cost"],
    "materials": ["material", "materials", "ashby", "asm", "steel", "aluminum", "plastic", "abs", "pc", "pp", "nylon", "strength", "stiffness", "density", "corrosion", "datasheet"],
    "patent": ["patent", "prior art", "claim", "innovation", "invention", "triz", "novelty", "prototype", "wipo", "uspto"],
}

DEFAULT_PACKS: Dict[str, Dict[str, List[str]]] = {
    "mechanical_design": {
        "refs": ["Shigley's Mechanical Engineering Design", "Roark's Formulas for Stress and Strain", "Machinery's Handbook", "ASME Y14.5 GD&T principles", "NASA Systems Engineering Handbook"],
        "rules": ["Define loads, constraints, materials, environment, safety factor, and validation method.", "Check manufacturability, tolerance stack-up, failure modes, and test plan before final design.", "Use hand calculations as sanity checks before simulation."],
    },
    "cad_solidworks": {
        "refs": ["SolidWorks API Help", "SolidWorks VBA macro examples", "Engineering drawing standards", "STEP/DXF export practices"],
        "rules": ["Prefer parametric, editable CAD models.", "Separate geometry creation, features, drawings, BOM, and exports.", "Warn before destructive macros or file overwrites."],
    },
    "simulation_fea": {
        "refs": ["ANSYS Theory Reference", "NAFEMS verification and validation principles", "Cook: Concepts and Applications of Finite Element Analysis", "Practical FEA best practices"],
        "rules": ["Define the simulation objective before setup.", "Check load paths, constraints, contacts, mesh quality, and convergence.", "Validate FEA with hand calculations, test data, or benchmark cases."],
    },
    "cfd_thermal": {
        "refs": ["Versteeg and Malalasekera: An Introduction to CFD", "ANSYS Fluent Theory Guide", "Incropera: Fundamentals of Heat and Mass Transfer", "Fox and McDonald: Fluid Mechanics", "White: Fluid Mechanics"],
        "rules": ["Identify flow regime using Reynolds number before model selection.", "Check boundary conditions, mesh quality, y plus, convergence, and conservation balances.", "Validate CFD with analytical estimates or experimental data."],
    },
    "manufacturing_dfm": {
        "refs": ["Kalpakjian: Manufacturing Engineering and Technology", "SME Manufacturing Engineering Handbook", "Boothroyd Dewhurst DFA/DFM methodology", "Injection molding design guides", "Sheet metal and machining design guides"],
        "rules": ["Match geometry to manufacturing process capability.", "Avoid unnecessary tight tolerances.", "Consider tooling, cycle time, scrap, inspection, assembly, and repeatability.", "Design for production stability, not prototype success only."],
    },
    "materials_selection": {
        "refs": ["Ashby: Materials Selection in Mechanical Design", "ASM Handbooks", "Supplier datasheets", "MatWeb-style material datasheet reasoning"],
        "rules": ["Start from functional requirements, not material preference.", "Compare stiffness, strength, toughness, density, thermal limits, corrosion, process compatibility, cost, and availability.", "Never select a material from strength alone.", "Always check manufacturing compatibility and supplier availability."],
    },
    "innovation_patent": {
        "refs": ["TRIZ methodology", "WIPO prior-art search approach", "USPTO classification logic", "Prototype validation planning", "Patent claim drafting checklists"],
        "rules": ["Separate novelty, usefulness, manufacturability, and commercial value.", "Search prior art before heavy development investment.", "Convert ideas into testable claims and prototype requirements.", "Avoid giving legal certainty without patent attorney review."],
    },
}

@dataclass
class SearchHit:
    pack: str
    title: str
    source: str
    score: float
    rules: List[str]
    refs: List[str]


def seed_knowledge_packs() -> None:
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    for pack, data in DEFAULT_PACKS.items():
        folder = KNOWLEDGE_DIR / pack
        folder.mkdir(parents=True, exist_ok=True)
        notes = folder / "notes.md"
        if not notes.exists():
            text = f"# {PACK_TITLES[pack]} Knowledge Pack\n\n## Core references\n"
            text += "\n".join(f"- {x}" for x in data["refs"])
            text += "\n\n## Engineering rules\n"
            text += "\n".join(f"- {x}" for x in data["rules"])
            text += "\n"
            notes.write_text(text, encoding="utf-8")


def extract_list_after_heading(text: str, heading: str) -> List[str]:
    pattern = re.compile(rf"##\s*{re.escape(heading)}\s*(.*?)(?=\n##\s|\Z)", re.S | re.I)
    match = pattern.search(text)
    if not match:
        return []
    items: List[str] = []
    for line in match.group(1).splitlines():
        line = line.strip()
        if line.startswith("-"):
            items.append(line.lstrip("- ").strip())
    return items


def route_workspace(question: str, selected: str) -> str:
    q = question.lower()
    scores = {k: 0 for k in INTENT_KEYWORDS}
    for key, words in INTENT_KEYWORDS.items():
        for w in words:
            if w in q:
                scores[key] += 2 if len(w) > 4 else 1
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return selected or "chief"


def load_pack(pack: str) -> Tuple[List[str], List[str], str]:
    path = KNOWLEDGE_DIR / pack / "notes.md"
    if not path.exists():
        return [], [], str(path)
    text = path.read_text(encoding="utf-8", errors="ignore")
    return extract_list_after_heading(text, "Engineering rules"), extract_list_after_heading(text, "Core references"), str(path)


def search_internal(question: str, selected_workspace: str, top_k: int = 3) -> Tuple[str, List[SearchHit]]:
    routed = route_workspace(question, selected_workspace)
    preferred = WORKSPACE_TO_PACK.get(routed, "")
    q_tokens = set(re.findall(r"[a-zA-Z0-9+]+", question.lower()))
    hits: List[SearchHit] = []
    for pack in PACK_TITLES:
        rules, refs, source = load_pack(pack)
        blob = " ".join([pack, PACK_TITLES[pack], *rules, *refs]).lower()
        score = float(sum(1 for t in q_tokens if t and t in blob))
        if pack == preferred:
            score += 8.0
        if score > 0:
            hits.append(SearchHit(pack=pack, title=PACK_TITLES[pack], source=source, score=score, rules=rules, refs=refs))
    hits.sort(key=lambda h: h.score, reverse=True)
    return routed, hits[:top_k]


def source_block(hits: List[SearchHit]) -> str:
    if not hits:
        return "**Internal sources used**\n- No internal source matched strongly. Add more documents to `knowledge_packs`."
    lines = ["**Internal sources used**"]
    for i, h in enumerate(hits, 1):
        rel = h.source.replace(str(APP_DIR) + "\\", "").replace(str(APP_DIR) + "/", "")
        lines.append(f"- [K{i}] {h.title} — `{rel}`")
    return "\n".join(lines)


def answer_from_internal(question: str, selected_workspace: str) -> Tuple[str, str]:
    routed, hits = search_internal(question, selected_workspace)
    primary = hits[0] if hits else None
    rules = primary.rules if primary else []
    src = source_block(hits)

    if routed == "manufacturing":
        answer = """
**Internal Knowledge Only — Manufacturing / DFM starting review**

For an injection-molded plastic cover, treat this as a preliminary DFM checklist until CAD geometry, material, target volume, cosmetic requirements, and production process details are known.

**Assumptions to confirm**
- Part role: cosmetic cover, protective enclosure, or load-bearing cover.
- Material family: ABS, PP, PC, PA, or blend; this affects shrinkage, wall thickness, heat resistance, and impact performance.
- Production volume, surface class, assembly method, and expected environment.

**DFM checks**
1. **Wall thickness:** keep it as uniform as possible; abrupt thickness changes increase sink, warpage, and differential cooling.
2. **Draft:** add draft on vertical walls, ribs, and bosses so the tool releases cleanly.
3. **Ribs and bosses:** use ribs for stiffness instead of thick solid sections; avoid over-thick bosses that create sink marks.
4. **Corners and radii:** use generous internal radii to reduce stress concentration and improve flow.
5. **Gating and flow:** avoid long thin flow paths and place gates to reduce weld lines in critical or cosmetic zones.
6. **Tolerances:** avoid tight tolerances unless functionally required; injection molding variation depends on material, mold temperature, and process control.
7. **Assembly:** design snap fits, screws, heat staking, or clips with tool access and repeatability in mind.
8. **Validation:** confirm with mold-flow review, prototype checks, dimensional inspection, and assembly testing.
"""
    elif routed == "solidworks":
        answer = """
**Internal Knowledge Only — CAD / SolidWorks guidance**

Use a parametric workflow: define reference planes, sketches, named dimensions, features, drawing outputs, and export targets separately.

**Recommended approach**
- Create editable sketches and avoid hard-coded geometry when automation is expected.
- Separate part creation, drawing creation, BOM extraction, and STEP/DXF export into clear macro sections.
- Add a safety confirmation before overwriting files or modifying open assemblies.
"""
    elif routed == "fea":
        answer = """
**Internal Knowledge Only — FEA setup guidance**

Start by defining the engineering decision the simulation must support. A stress plot alone is not enough.

**Minimum FEA checklist**
- Define load cases, constraints, contacts, material model, and acceptance criteria.
- Check load paths and whether constraints over-stiffen the structure.
- Run mesh convergence and compare against hand calculations where possible.
- Validate the setup before using results for design release.
"""
    elif routed == "cfd":
        answer = """
**Internal Knowledge Only — CFD / Thermal guidance**

Start with the flow regime and heat-transfer objective before choosing software settings.

**Minimum CFD checklist**
- Estimate Reynolds number and pressure drop before CFD.
- Define inlet, outlet, wall, thermal, and symmetry conditions clearly.
- Check mesh quality, y plus target, inflation layers, residuals, and conservation balances.
- Validate CFD with analytical estimates or test data.
"""
    elif routed == "materials":
        answer = """
**Internal Knowledge Only — Materials selection guidance**

Do not select material by strength alone. Begin with functional requirements and manufacturing route.

**Selection checklist**
- Mechanical: stiffness, yield/ultimate strength, toughness, fatigue, creep.
- Environmental: temperature, UV, humidity, chemicals, corrosion.
- Manufacturing: injection molding, machining, forming, welding, joining, availability.
- Cost: material price, scrap, cycle time, tooling, supplier stability.
"""
    elif routed == "patent":
        answer = """
**Internal Knowledge Only — Innovation / Patent guidance**

Separate technical novelty from commercial value and manufacturing feasibility.

**Early innovation checklist**
- Define the problem solved and the exact inventive mechanism.
- Search prior art before major investment.
- Convert the idea into prototype requirements and measurable tests.
- Do not treat this as legal advice; use a patent attorney for filing strategy.
"""
    else:
        answer = """
**Internal Knowledge Only — Chief Engineer starting point**

I will answer using the internal MechAI knowledge packs first. For a stronger engineering answer, provide geometry, material, loads, manufacturing route, target volume, constraints, and acceptance criteria.
"""

    if rules:
        answer += "\n**Internal rules applied**\n" + "\n".join(f"- {r}" for r in rules[:4]) + "\n"
    answer += "\n" + src
    answer += "\n\n**Engineering use note:** this is internal guidance, not certified professional engineering verification. Validate assumptions, calculations, standards compliance, and test evidence before release."
    return routed, answer.strip()


def inject_css() -> None:
    st.markdown("""
<style>
:root { --bg:#000; --panel:#050505; --muted:#9b9b9b; --border:#262626; --text:#f5f5f5; }
html, body, [data-testid="stAppViewContainer"] { background:#000 !important; color:var(--text); }
[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer { visibility:hidden !important; height:0 !important; }
[data-testid="stSidebar"] { background:#000 !important; border-right:1px solid #202020; min-width:300px !important; max-width:300px !important; }
[data-testid="stSidebar"] * { color:#f4f4f4; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#a8a8a8; }
.stButton > button { border-radius:12px !important; background:#303030 !important; border:1px solid #303030 !important; color:#fff !important; height:46px; }
.stSelectbox div[data-baseweb="select"] > div { background:#111 !important; border:1px solid #2a2a2a !important; border-radius:12px !important; }
[data-testid="stExpander"] { background:#030303 !important; border:1px solid #252525 !important; border-radius:12px !important; }
.block-container { max-width:980px !important; padding-top:2rem !important; padding-bottom:8rem !important; }
[data-testid="stChatInput"] { background:#101114 !important; border-top:1px solid #151515 !important; }
[data-testid="stChatInput"] textarea { background:#202020 !important; border-radius:28px !important; color:white !important; }
.small-muted { color:#8c8c8c; font-size:0.88rem; }
.version { color:#777; font-size:0.75rem; }
</style>
""", unsafe_allow_html=True)


st.set_page_config(page_title="MechAI Pro", page_icon="⚙️", layout="wide", initial_sidebar_state="expanded")
inject_css()
seed_knowledge_packs()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "workspace" not in st.session_state:
    st.session_state.workspace = "chief"
if "project" not in st.session_state:
    st.session_state.project = "RD_Lab"

with st.sidebar:
    st.markdown("## MechAI Pro")
    if st.button("✎ New chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("⌕ Search chats")
    st.markdown("▥ Library")
    st.markdown("### Workspace")
    labels = list(WORKSPACES.values())
    current_label = WORKSPACES.get(st.session_state.workspace, labels[0])
    chosen = st.selectbox("Workspace", labels, index=labels.index(current_label), label_visibility="collapsed")
    st.session_state.workspace = [k for k, v in WORKSPACES.items() if v == chosen][0]
    st.caption("Workspace biases the internal knowledge search. MechAI still auto-routes from your question.")
    st.markdown("### View")
    view = st.radio("View", ["Chat", "About"], horizontal=True, label_visibility="collapsed")
    st.markdown("### Projects")
    st.session_state.project = st.selectbox("Project", ["RD_Lab"], label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        st.button("+ Project", use_container_width=True)
    with c2:
        if st.button("Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with st.expander("Settings", expanded=False):
        st.caption("Mode: Internal Knowledge Only")
        st.caption(f"Internal knowledge packs: {len(PACK_TITLES)}")
        st.caption("External AI providers are not part of this build.")
        st.caption(f"Build: {BUILD_ID}")
    st.markdown("---")
    st.caption("Wafeeq · MechAI Pro")

if view == "About":
    st.markdown("# MechAI Pro")
    st.markdown("""
**MechAI Pro** is a knowledge-first mechanical engineering copilot.

This clean build does **not** expose OpenAI, ChatGPT, Gemini, or external AI provider controls. The reference brain is the local `knowledge_packs` folder.

Current workspaces:
- Product R&D / Mechanical Design
- CAD / SolidWorks
- Simulation / FEA
- CFD / Thermal
- Manufacturing / DFM
- Materials Selection
- Innovation / Patent

Use note: outputs are engineering guidance, not certified calculations or compliance approval.
""")
    st.stop()

if not st.session_state.messages:
    st.markdown("<div style='height:25vh'></div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;font-weight:500'>Good to see you, Wafeeq.</h2>", unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

prompt = st.chat_input("Ask anything engineering…")
if prompt:
    st.session_state.messages.append({"role":"user", "content":prompt})
    routed, answer = answer_from_internal(prompt, st.session_state.workspace)
    agent_label = WORKSPACES.get(routed, "🧠 General engineering")
    final = f"_{agent_label} · Internal Knowledge Only_\n\n{answer}"
    st.session_state.messages.append({"role":"assistant", "content":final})
    st.rerun()
