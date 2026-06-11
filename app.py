# -*- coding: utf-8 -*-
"""
MechAI Pro v19 — Internal Knowledge Only UI
- Internal knowledge packs are the primary source and the only visible answer engine.
- OpenAI/Gemini UI is removed from the public app.
- External AI can be reintroduced later as a separate optional tool, not as the reference brain.
- Fixed sidebar, minimal ChatGPT-like UI.
Run: streamlit run app.py
"""
from __future__ import annotations

import os
import re
import html
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import streamlit as st

# External AI providers are intentionally hidden/disabled in this public knowledge-first build.
OpenAI = None
genai = None

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

APP_DIR = Path(__file__).parent
KNOWLEDGE_DIR = APP_DIR / "knowledge_packs"
PROJECTS_DIR = APP_DIR / "projects"
LOCAL_SAVE_ENABLED = os.getenv("MECHAI_ENABLE_LOCAL_SAVE", "false").strip().lower() == "true"

# -----------------------------------------------------------------------------
# Knowledge packs seed
# -----------------------------------------------------------------------------
DEFAULT_PACKS: Dict[str, Dict[str, object]] = {
    "mechanical_design": {
        "title": "Mechanical Design",
        "refs": ["Shigley's Mechanical Engineering Design", "Roark's Formulas for Stress and Strain", "Machinery's Handbook", "ASME Y14.5 GD&T principles", "NASA Systems Engineering Handbook"],
        "rules": ["Define loads, constraints, materials, environment, safety factor, and validation method.", "Check manufacturability, tolerance stack-up, failure modes, and test plan before final design.", "Use hand calculations as sanity checks before simulation."],
    },
    "cad_solidworks": {
        "title": "CAD / SolidWorks",
        "refs": ["SolidWorks API Help", "SolidWorks VBA macro examples", "Engineering drawing standards", "STEP/DXF export practices"],
        "rules": ["Prefer parametric, editable CAD models.", "Separate geometry creation, features, drawings, BOM, and exports.", "Warn before destructive macros or file overwrites."],
    },
    "simulation_fea": {
        "title": "Simulation / FEA",
        "refs": ["ANSYS Theory Reference", "NAFEMS verification and validation principles", "Cook: Concepts and Applications of Finite Element Analysis", "Practical FEA best practices"],
        "rules": ["Define the simulation objective before setup.", "Check load paths, constraints, contacts, mesh quality, and convergence.", "Validate FEA with hand calculations, test data, or benchmark cases."],
    },
    "cfd_thermal": {
        "title": "CFD / Thermal",
        "refs": ["Versteeg and Malalasekera: An Introduction to CFD", "ANSYS Fluent Theory Guide", "Incropera: Fundamentals of Heat and Mass Transfer", "Fox and McDonald: Fluid Mechanics", "White: Fluid Mechanics"],
        "rules": ["Identify flow regime using Reynolds number before model selection.", "Check boundary conditions, mesh quality, y plus, convergence, and conservation balances.", "Validate CFD with analytical estimates or experimental data."],
    },
    "manufacturing_dfm": {
        "title": "Manufacturing / DFM",
        "refs": ["Kalpakjian: Manufacturing Engineering and Technology", "SME Manufacturing Engineering Handbook", "Boothroyd Dewhurst DFA/DFM methodology", "Injection molding design guides", "Sheet metal and machining design guides"],
        "rules": ["Match geometry to manufacturing process capability.", "Avoid unnecessary tight tolerances.", "Consider tooling, cycle time, scrap, inspection, assembly, and repeatability.", "Design for production stability, not prototype success only."],
    },
    "materials_selection": {
        "title": "Materials Selection",
        "refs": ["Ashby: Materials Selection in Mechanical Design", "ASM Handbooks", "Supplier datasheets", "MatWeb-style material datasheet reasoning"],
        "rules": ["Start from functional requirements, not material preference.", "Compare stiffness, strength, toughness, density, thermal limits, corrosion, process compatibility, cost, and availability.", "Never select a material from strength alone.", "Always check manufacturing compatibility and supplier availability."],
    },
    "innovation_patent": {
        "title": "Innovation / Patent",
        "refs": ["TRIZ methodology", "WIPO prior-art search approach", "USPTO classification logic", "Prototype validation planning", "Patent claim drafting checklists"],
        "rules": ["Separate novelty, usefulness, manufacturability, and commercial value.", "Search prior art before heavy development investment.", "Convert ideas into testable claims and prototype requirements.", "Avoid giving legal certainty without patent attorney review."],
    },
}

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

AGENTS = {
    "chief": "🧠 Chief Engineer",
    "mechanical": "🔧 Mechanical Design",
    "solidworks": "🧩 CAD / SolidWorks",
    "fea": "📊 FEA Simulation",
    "cfd": "🌊 CFD & Thermal",
    "manufacturing": "🏭 Manufacturing DFM/DFA",
    "materials": "🧪 Materials Selection",
    "patent": "💡 Innovation / Patent",
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

@dataclass
class KnowledgeDoc:
    pack: str
    title: str
    path: str
    refs: List[str]
    rules: List[str]
    raw: str

@dataclass
class KnowledgeHit:
    pack: str
    title: str
    path: str
    score: float
    refs: List[str]
    rules: List[str]


def seed_knowledge_packs() -> None:
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    for pack, data in DEFAULT_PACKS.items():
        p = KNOWLEDGE_DIR / pack
        p.mkdir(parents=True, exist_ok=True)
        (p / "source_docs").mkdir(exist_ok=True)
        notes = p / "notes.md"
        if not notes.exists():
            lines = [f"# {data['title']} Knowledge Pack", "", "## Core references"]
            lines += [f"- {r}" for r in data["refs"]]
            lines += ["", "## Engineering rules"]
            lines += [f"- {r}" for r in data["rules"]]
            notes.write_text("\n".join(lines) + "\n", encoding="utf-8")


def extract_bullets(text: str, section: str) -> List[str]:
    lines = text.splitlines()
    target = section.strip().lower()
    active = False
    out: List[str] = []
    for line in lines:
        s = line.strip()
        normalized = re.sub(r"^#+\s*", "", s).strip().lower().rstrip(":")
        if normalized == target:
            active = True
            continue
        if active and s.startswith("#"):
            break
        if active and s.startswith("-"):
            item = re.sub(r"^[-\s]+", "", s).strip()
            if item:
                out.append(item)
    return out


def pack_display_name(pack: str) -> str:
    return str(DEFAULT_PACKS.get(pack, {}).get("title", pack.replace("_", " ").title()))


def load_docs() -> List[KnowledgeDoc]:
    seed_knowledge_packs()
    docs: List[KnowledgeDoc] = []
    for notes in sorted(KNOWLEDGE_DIR.glob("*/notes.md")):
        pack = notes.parent.name
        raw = notes.read_text(encoding="utf-8", errors="ignore")
        refs = extract_bullets(raw, "Core references")
        rules = extract_bullets(raw, "Engineering rules")
        docs.append(KnowledgeDoc(pack=pack, title=pack_display_name(pack), path=str(notes).replace("\\", "/"), refs=refs, rules=rules, raw=raw))
    return docs


def tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9\+\#\.\-/]+|[\u0600-\u06FF]+", text.lower())


def infer_agent(query: str) -> str:
    q = query.lower()
    best_agent = "chief"
    best = 0
    for agent, words in INTENT_KEYWORDS.items():
        score = 0
        for w in words:
            if w in q:
                score += 3 if " " in w else 1
        if score > best:
            best = score
            best_agent = agent
    return best_agent


def route_agent(query: str, selected_workspace: str) -> str:
    inferred = infer_agent(query)
    if inferred != "chief":
        return inferred
    return selected_workspace or "chief"


def retrieve_knowledge(query: str, agent: str, top_k: int = 3) -> List[KnowledgeHit]:
    docs = load_docs()
    q_tokens = set(tokens(query))
    preferred_pack = WORKSPACE_TO_PACK.get(agent, "")
    inferred_pack = WORKSPACE_TO_PACK.get(infer_agent(query), "")
    hits: List[KnowledgeHit] = []
    for doc in docs:
        raw_tokens = set(tokens(doc.raw + " " + " ".join(doc.refs) + " " + " ".join(doc.rules)))
        score = float(len(q_tokens & raw_tokens))
        phrase_bonus = 0.0
        q = query.lower()
        if "injection" in q and "molding" in q and doc.pack == "manufacturing_dfm": phrase_bonus += 8
        if "dfm" in q and doc.pack == "manufacturing_dfm": phrase_bonus += 8
        if "solidworks" in q and doc.pack == "cad_solidworks": phrase_bonus += 8
        if "fea" in q or "ansys" in q:
            if doc.pack == "simulation_fea": phrase_bonus += 8
        if "cfd" in q or "thermal" in q or "reynolds" in q:
            if doc.pack == "cfd_thermal": phrase_bonus += 8
        if "material" in q or "abs" in q or "plastic" in q:
            if doc.pack == "materials_selection": phrase_bonus += 4
        score += phrase_bonus
        if preferred_pack and doc.pack == preferred_pack:
            score *= 1.25
        if inferred_pack and doc.pack == inferred_pack:
            score *= 1.35
        if score > 0:
            hits.append(KnowledgeHit(pack=doc.pack, title=doc.title, path=doc.path, score=round(score, 3), refs=doc.refs[:4], rules=doc.rules[:6]))
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:top_k]


def sources_block(hits: List[KnowledgeHit]) -> str:
    if not hits:
        return ""
    lines = ["**Internal sources used**"]
    for i, h in enumerate(hits, 1):
        lines.append(f"- [K{i}] {h.title} — `{h.path}`")
    return "\n".join(lines)


def rules_for(hits: List[KnowledgeHit], pack: str, fallback: List[str]) -> List[str]:
    for h in hits:
        if h.pack == pack and h.rules:
            return h.rules
    return fallback


def compose_internal_answer(query: str, agent: str, hits: List[KnowledgeHit]) -> str:
    q = query.lower()
    src = sources_block(hits)
    if agent == "manufacturing" or any(w in q for w in ["dfm", "dfa", "injection", "molding", "manufacturing", "tooling"]):
        rules = rules_for(hits, "manufacturing_dfm", DEFAULT_PACKS["manufacturing_dfm"]["rules"])
        return (
            "**Internal Knowledge Only — Manufacturing / DFM starting review**\n\n"
            "For an injection-molded plastic cover, treat this as a preliminary DFM checklist until CAD geometry, material, target tolerance class, cosmetic requirements, and production volume are known.\n\n"
            "**Assumptions to confirm**\n"
            "- Part role: cosmetic cover, protective enclosure, or load-bearing cover.\n"
            "- Material family: ABS, PP, PC, PA, or blend; this affects shrinkage, wall thickness, heat resistance, and impact behavior.\n"
            "- Production volume, surface class, assembly method, and expected environment.\n\n"
            "**DFM checks**\n"
            "1. **Wall thickness:** keep it as uniform as possible; abrupt thickness changes increase sink, warpage, and differential cooling.\n"
            "2. **Draft:** add draft on vertical walls, ribs, and bosses so the tool releases cleanly.\n"
            "3. **Ribs and bosses:** use ribs for stiffness instead of thick solid sections; avoid over-thick bosses that create sink marks.\n"
            "4. **Radii and corners:** add internal radii to improve flow and reduce stress concentration.\n"
            "5. **Gate and flow path:** avoid weld lines on visible or high-stress regions; reserve practical gate and ejector locations.\n"
            "6. **Tolerances:** avoid tight plastic tolerances unless function requires them; they increase tooling, inspection, and scrap cost.\n"
            "7. **Assembly:** review screws, snap-fits, inserts, sealing ribs, datum scheme, and tool access.\n\n"
            "**Internal rules applied**\n" + "\n".join(f"- {r}" for r in rules[:4]) + "\n\n"
            "**Next data needed for a real review**\n"
            "- CAD image/STEP, material, nominal wall thickness, expected annual volume, assembly method, target surface finish, and critical dimensions.\n\n"
            f"{src}\n\n"
            "**Engineering use note:** this is internal guidance, not certified production approval. Validate mold-flow risks, tolerances, tooling assumptions, and test evidence before release."
        )
    if agent == "solidworks":
        rules = rules_for(hits, "cad_solidworks", DEFAULT_PACKS["cad_solidworks"]["rules"])
        return "**Internal Knowledge Only — CAD / SolidWorks guidance**\n\n" + "\n".join(f"- {r}" for r in rules) + f"\n\n{src}"
    if agent == "fea":
        rules = rules_for(hits, "simulation_fea", DEFAULT_PACKS["simulation_fea"]["rules"])
        return "**Internal Knowledge Only — FEA setup guidance**\n\n" + "\n".join(f"- {r}" for r in rules) + f"\n\n{src}"
    if agent == "cfd":
        rules = rules_for(hits, "cfd_thermal", DEFAULT_PACKS["cfd_thermal"]["rules"])
        return "**Internal Knowledge Only — CFD / Thermal guidance**\n\n" + "\n".join(f"- {r}" for r in rules) + f"\n\n{src}"
    if agent == "materials":
        rules = rules_for(hits, "materials_selection", DEFAULT_PACKS["materials_selection"]["rules"])
        return "**Internal Knowledge Only — Materials selection guidance**\n\n" + "\n".join(f"- {r}" for r in rules) + f"\n\n{src}"
    if agent == "patent":
        rules = rules_for(hits, "innovation_patent", DEFAULT_PACKS["innovation_patent"]["rules"])
        return "**Internal Knowledge Only — Innovation / Patent guidance**\n\n" + "\n".join(f"- {r}" for r in rules) + "\n\nNot legal advice. Use a patent attorney for filing decisions.\n\n" + src
    rules = []
    for h in hits:
        rules.extend(h.rules[:2])
    if not rules:
        rules = ["Clarify the engineering objective, constraints, loads, materials, manufacturing process, and validation method."]
    return "**Internal Knowledge Only — Chief Engineer starting point**\n\n" + "\n".join(f"- {r}" for r in rules[:6]) + f"\n\n{src}"


def knowledge_context_for_ai(hits: List[KnowledgeHit]) -> str:
    lines = []
    for i, h in enumerate(hits, 1):
        lines.append(f"[K{i}] {h.title} ({h.path})")
        for r in h.rules[:4]:
            lines.append(f"- {r}")
    return "\n".join(lines) if lines else "No internal knowledge source found."

# -----------------------------------------------------------------------------
# External AI optional
# -----------------------------------------------------------------------------
def get_secret(name: str) -> str:
    try:
        return st.secrets.get(name, "") or os.getenv(name, "")
    except Exception:
        return os.getenv(name, "") or ""


def external_polish(internal_answer: str, query: str, hits: List[KnowledgeHit], provider: str) -> str:
    prompt = f"""You are MechAI Pro. Polish and organize the following internal-knowledge answer without adding unsupported facts. Keep sources.\n\nQuestion: {query}\n\nInternal sources:\n{knowledge_context_for_ai(hits)}\n\nDraft answer:\n{internal_answer}"""
    if provider.startswith("OpenAI") and OpenAI and get_secret("OPENAI_API_KEY"):
        try:
            client = OpenAI(api_key=get_secret("OPENAI_API_KEY"))
            resp = client.responses.create(model="gpt-4o-mini", input=prompt)
            return "_Internal knowledge first; OpenAI used only for organization/polish._\n\n" + (getattr(resp, "output_text", "") or str(resp))
        except Exception:
            return internal_answer
    if provider.startswith("Gemini") and genai and get_secret("GEMINI_API_KEY"):
        try:
            client = genai.Client(api_key=get_secret("GEMINI_API_KEY"))
            resp = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt)
            return "_Internal knowledge first; Gemini used only for organization/polish._\n\n" + (getattr(resp, "text", "") or str(resp))
        except Exception:
            return internal_answer
    return internal_answer

# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------
st.set_page_config(page_title="MechAI Pro", page_icon="⚙️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;}
.stApp{background:#000;color:#f4f4f4;}
#MainMenu, footer, header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton{display:none!important;visibility:hidden!important;height:0!important;}
[data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"], button[kind="header"]{display:none!important;visibility:hidden!important;}
[data-testid="stSidebar"]{background:#050505!important;border-right:1px solid #222!important;min-width:292px!important;max-width:292px!important;width:292px!important;position:fixed!important;left:0!important;top:0!important;bottom:0!important;height:100vh!important;transform:none!important;visibility:visible!important;z-index:999!important;overflow-y:auto!important;}
.block-container{max-width:980px!important;padding:2rem 2rem 8rem!important;margin-left:292px!important;}
.sidebar-title{font-size:22px;font-weight:750;margin:18px 0 26px;color:#fff;}
.side-label{color:#888;font-weight:700;font-size:12px;margin:22px 0 8px;}
.nav-btn{padding:10px 12px;border-radius:10px;margin:4px 0;color:#eee;font-size:14px;}
.nav-btn:hover{background:#202020;}
[data-testid="stSidebar"] .stButton button{width:100%;height:42px;border-radius:10px;border:0;background:#2f2f2f;color:#fff;font-weight:500;}
[data-testid="stSidebar"] .stButton button:hover{background:#3a3a3a;}
[data-testid="stSelectbox"] div[data-baseweb="select"]>div,[data-testid="stTextInput"] input{background:#111!important;border:1px solid #2a2a2a!important;color:#fff!important;border-radius:10px!important;min-height:42px;}
[data-testid="stSidebar"] label{color:#888!important;font-weight:650!important;font-size:12px!important;}
.note{color:#8b8b8b;font-size:12px;line-height:1.45;margin:8px 0 14px;}
.user-chip{position:fixed;bottom:12px;left:12px;width:260px;border-top:1px solid #222;padding-top:10px;color:#ddd;font-size:13px;background:#050505;}
.landing{min-height:64vh;display:flex;align-items:center;justify-content:center;text-align:center;}
.landing h1{font-size:24px;font-weight:500;color:#f4f4f4;}
.message-row{display:grid;grid-template-columns:40px minmax(0,1fr);gap:14px;margin:24px auto;max-width:920px;}
.avatar{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:15px;background:#232323;color:#fff;}
.avatar.user{background:#7c3aed}.avatar.ai{background:#202020;border:1px solid #333;}
.bubble{font-size:16px;line-height:1.75;color:#f4f4f4;overflow-wrap:anywhere;}
.bubble.user{font-weight:650;line-height:1.4;padding-top:3px;}
.agent-tag{color:#aaa;font-size:13px;margin-bottom:18px;}
.footer-note{position:fixed;left:292px;right:0;bottom:8px;text-align:center;color:#666;font-size:11px;pointer-events:none;}
[data-testid="stChatInput"]{position:fixed!important;left:calc(292px + 8vw)!important;right:8vw!important;bottom:32px!important;z-index:1001!important;background:#2b2b31!important;border:1px solid #3a3a42!important;border-radius:12px!important;padding:12px 14px!important;box-shadow:0 18px 40px rgba(0,0,0,.45)!important;}
[data-testid="stChatInput"] textarea{background:#212121!important;border:1px solid #3b3b3b!important;border-radius:999px!important;color:#f4f4f4!important;min-height:52px!important;padding:15px 58px 15px 20px!important;font-size:15px!important;}
[data-testid="stChatInput"] button{background:#f4f4f4!important;color:#000!important;border-radius:50%!important;width:38px!important;height:38px!important;}
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3{font-size:inherit!important;line-height:1.75!important;margin:0!important;}
.stMarkdown p,.stMarkdown li{font-size:16px!important;line-height:1.75!important;}
.stMarkdown code{font-size:13px!important;background:#161616!important;border:1px solid #2a2a2a!important;border-radius:5px!important;padding:1px 5px!important;}
@media(max-width:900px){[data-testid="stSidebar"]{position:relative!important;width:100%!important;max-width:100%!important;min-width:100%!important;height:auto!important}.block-container{margin-left:0!important;padding:1rem 1rem 8rem!important}[data-testid="stChatInput"]{left:1rem!important;right:1rem!important}.footer-note{left:0!important}.user-chip{position:static;width:auto;margin-top:18px}}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# State
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "workspace" not in st.session_state:
    st.session_state.workspace = "chief"
if "view" not in st.session_state:
    st.session_state.view = "Chat"
if "answer_mode" not in st.session_state:
    st.session_state.answer_mode = "Internal Knowledge Only"
if "project" not in st.session_state:
    st.session_state.project = "RD_Lab"

# Auto-clean old raw answers from earlier builds.
def looks_like_old_raw(m: dict) -> bool:
    c = str(m.get("content", ""))
    return "Internal knowledge retrieved:" in c or ("Pack:" in c and "Score:" in c and "Knowledge Pack ##" in c)
if any(looks_like_old_raw(m) for m in st.session_state.messages):
    st.session_state.messages = []

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">MechAI Pro</div>', unsafe_allow_html=True)
    if st.button("✎  New chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown('<div class="nav-btn">⌕&nbsp;&nbsp;Search chats</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-btn">▥&nbsp;&nbsp;Library</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-label">Workspace</div>', unsafe_allow_html=True)
    ws_keys = list(WORKSPACES.keys())
    ws_labels = [WORKSPACES[k] for k in ws_keys]
    current_idx = ws_keys.index(st.session_state.workspace) if st.session_state.workspace in ws_keys else 0
    selected_label = st.selectbox("Workspace", ws_labels, index=current_idx, label_visibility="collapsed")
    st.session_state.workspace = ws_keys[ws_labels.index(selected_label)]
    st.markdown('<div class="note">Workspace biases the internal knowledge search. MechAI still auto-routes from your question.</div>', unsafe_allow_html=True)

    st.session_state.view = st.radio("View", ["Chat", "About"], horizontal=True, index=0 if st.session_state.view == "Chat" else 1)

    st.markdown('<div class="side-label">Projects</div>', unsafe_allow_html=True)
    st.selectbox("Project", [st.session_state.project], label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("+ Project", use_container_width=True):
            st.session_state.project = f"Project_{datetime.now().strftime('%H%M')}"
            st.session_state.messages = []
            st.rerun()
    with c2:
        if st.button("Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with st.expander("Settings", expanded=False):
        st.caption("Mode: Internal Knowledge Only")
        st.caption(f"Internal knowledge packs: {len(load_docs())}")
        st.caption("External AI providers are hidden in this build. The reference brain is knowledge_packs.")
    st.markdown('<div class="user-chip">Wafeeq · MechAI Pro</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if st.session_state.view == "About":
    st.markdown("""
**MechAI Pro** is a knowledge-first mechanical engineering copilot prototype.

Primary source: internal workspace knowledge packs. OpenAI/Gemini are not visible in this public build and are not the reference brain.

Public demo warning: do not upload confidential files. Verify all calculations, CAD scripts, simulation assumptions, standards compliance, and safety-critical claims before engineering use.
""")
else:
    if not st.session_state.messages:
        st.markdown('<div class="landing"><h1>Good to see you, Wafeeq.</h1></div>', unsafe_allow_html=True)
    else:
        for m in st.session_state.messages:
            role = m.get("role", "assistant")
            content = str(m.get("content", ""))
            if role == "user":
                st.markdown(f'<div class="message-row"><div class="avatar user">☻</div><div class="bubble user">{html.escape(content)}</div></div>', unsafe_allow_html=True)
            else:
                agent = m.get("agent", "chief")
                mode = m.get("mode", st.session_state.answer_mode)
                st.markdown(f'<div class="message-row"><div class="avatar ai">⚙</div><div class="bubble ai"><div class="agent-tag">{html.escape(AGENTS.get(agent, AGENTS["chief"]))} · {html.escape(mode)}</div>', unsafe_allow_html=True)
                st.markdown(content)
                st.markdown('</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="footer-note">MechAI Pro · Public Demo · Knowledge-first mechanical engineering copilot · Verify all outputs before engineering use</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Execute query
# -----------------------------------------------------------------------------
user_prompt = st.chat_input("Ask anything engineering…")
if user_prompt:
    selected_ws = st.session_state.workspace
    agent = route_agent(user_prompt, selected_ws)
    hits = retrieve_knowledge(user_prompt, agent, top_k=3)
    answer = compose_internal_answer(user_prompt, agent, hits)
    st.session_state.answer_mode = "Internal Knowledge Only"
    st.session_state.messages.append({"role":"user", "content":user_prompt, "agent":agent})
    st.session_state.messages.append({"role":"assistant", "content":answer, "agent":agent, "mode":st.session_state.answer_mode})
    st.rerun()
