# -*- coding: utf-8 -*-
"""
MechAI Pro v6 Ultra Clean Chat UI
Ultra-clean ChatGPT-style Mechanical Engineering Copilot with minimal landing UI.
Run: streamlit run app_mechai_pro_v6_ultra_clean.py
"""
import os, json, re, uuid, math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import streamlit as st

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

APP_DIR = Path(__file__).parent
PROJECTS_DIR = APP_DIR / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="MechAI Pro", page_icon="⚙️", layout="wide", initial_sidebar_state="expanded")

# ----------------------------- CSS: Premium Chat-first UI -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{
  --bg:#070A12; --panel:#0D1321; --panel2:#111A2E; --line:#26334E; --muted:#9FB0D0;
  --text:#F7FAFF; --accent:#6EE7F9; --accent2:#A78BFA; --danger:#FF5A6A; --good:#30D98B;
}
html, body, [class*="css"] { font-family: Inter, system-ui, sans-serif; }
.stApp { background: radial-gradient(circle at 22% 0%, #18213D 0%, #070A12 36%, #05070D 100%); color:var(--text); }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#0B1020,#070A12); border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:var(--text); }
.block-container { max-width: 1500px; padding: 1.2rem 2rem 7rem 2rem; }
#MainMenu, footer, header { visibility: hidden; }
.hero-mini { display:flex; align-items:center; justify-content:space-between; border:1px solid #243550; background:linear-gradient(135deg,rgba(17,26,46,.96),rgba(9,18,31,.90)); border-radius:24px; padding:18px 22px; margin-bottom:16px; box-shadow:0 18px 50px rgba(0,0,0,.28); }
.brand { display:flex; gap:14px; align-items:center; }
.logo { width:44px; height:44px; border-radius:14px; display:grid; place-items:center; background:linear-gradient(135deg,var(--accent),var(--accent2)); color:#06101c; font-size:24px; font-weight:900; }
.brand h1 { font-size:26px; margin:0; letter-spacing:-.04em; }
.brand p { margin:2px 0 0 0; color:var(--muted); font-size:13px; }
.pillrow { display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }
.pill { border:1px solid #31405d; background:#111B2F; border-radius:999px; padding:8px 12px; font-size:12px; color:#DDE8FF; }
.sidebar-card { border:1px solid #28354F; background:linear-gradient(135deg,#111A2D,#0B1221); border-radius:20px; padding:16px; margin:10px 0 18px 0; }
.sidebar-title { font-size:19px; font-weight:800; margin-bottom:4px; }
.sidebar-sub { font-size:12px; color:#9FB0D0; line-height:1.6; }
.agent-chip { border:1px solid #31405d; background:#0D1526; border-radius:18px; padding:12px; margin:7px 0; }
.agent-chip .name { font-weight:750; font-size:14px; }
.agent-chip .desc { color:#9FB0D0; font-size:12px; margin-top:4px; }
.stButton>button { border-radius:14px; border:1px solid #34415B; background:linear-gradient(180deg,#17233B,#10182B); color:#F7FAFF; min-height:42px; font-weight:650; }
.stButton>button:hover { border-color:var(--accent); color:white; box-shadow:0 0 0 1px rgba(110,231,249,.25); }
[data-testid="stChatMessage"] { background:transparent; border:none; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"]{ font-size:15px; line-height:1.75; }
.chat-welcome { text-align:center; padding:96px 16px 28px 16px; }
.chat-welcome h2 { font-size:42px; letter-spacing:-.05em; margin:0 0 10px 0; }
.chat-welcome p { color:var(--muted); font-size:16px; margin:0 auto; max-width:720px; }
.quick-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin:18px auto 0 auto; max-width:900px; }
.quick-card { border:1px solid #28354F; background:rgba(17,26,46,.50); border-radius:16px; padding:12px; text-align:left; min-height:86px; }
.quick-card b { display:block; margin-bottom:8px; }
.quick-card span { color:#AEC0E1; font-size:12px; line-height:1.35; }
.right-panel { border:1px solid #28354F; background:rgba(9,15,28,.68); border-radius:20px; padding:14px; position:sticky; top:16px; }
.right-panel h3 { font-size:14px; margin:0 0 10px 0; color:#DDE8FF; }
.kv { display:flex; justify-content:space-between; gap:12px; border-bottom:1px solid rgba(255,255,255,.07); padding:9px 0; font-size:12px; }
.kv span:first-child{ color:#9FB0D0; } .kv span:last-child{ font-weight:700; }
.toolbox { border:1px solid #25324A; background:#0C1424; border-radius:14px; padding:12px; margin-top:10px; }
.toolbox-title { font-weight:750; font-size:13px; margin-bottom:6px; }
.toolbox-text { color:#9FB0D0; font-size:12px; line-height:1.55; }
.stChatInputContainer { background:rgba(8,11,18,.92)!important; border-top:1px solid rgba(255,255,255,.06); }
textarea, input, .stTextInput input, .stTextArea textarea { border-radius:14px!important; }
@media (max-width: 1100px){ .quick-grid{grid-template-columns:repeat(2,1fr);} .brand h1{font-size:20px;} }
</style>
""", unsafe_allow_html=True)

# ----------------------------- Localization -----------------------------
T = {
    "English": {
        "tagline":"Mechanical AI workspace for design, CAD automation, simulation, CFD, manufacturing, and invention.",
        "new_project":"+ New project", "save":"Save", "projects":"Projects", "settings":"Settings",
        "api":"Gemini API Key", "model":"Model", "lang":"Language", "welcome":"What would you like to engineer today?",
        "welcome_sub":"Ask a focused engineering question. MechAI routes it to the right specialist and uses your project memory and uploaded references.",
        "input":"Message MechAI Pro…", "right":"Engineering Studio", "brain":"Active Brain", "agent":"Routed Agent",
        "refs":"Reference Brain", "tools":"Tools", "upload":"Knowledge Vault", "vision":"Vision input", "project":"Current project",
        "no_key":"Add your Gemini API key in the sidebar or set GEMINI_API_KEY in PowerShell.",
    },
    "العربية": {
        "tagline":"مساحة ذكاء اصطناعي ميكانيكية للتصميم، الأتمتة، المحاكاة، الموائع، التصنيع، والاختراع.",
        "new_project":"+ مشروع جديد", "save":"حفظ", "projects":"المشاريع", "settings":"الإعدادات",
        "api":"مفتاح Gemini", "model":"الموديل", "lang":"اللغة", "welcome":"ماذا تريد أن تهندس اليوم؟",
        "welcome_sub":"اكتب سؤالًا هندسيًا واضحًا. MechAI يوجهه للوكيل المناسب ويستخدم ذاكرة المشروع والمراجع المرفوعة.",
        "input":"اكتب إلى MechAI Pro…", "right":"استوديو الهندسة", "brain":"العقل النشط", "agent":"الوكيل المختار",
        "refs":"العقل المرجعي", "tools":"الأدوات", "upload":"خزنة المعرفة", "vision":"إدخال بصري", "project":"المشروع الحالي",
        "no_key":"أضف مفتاح Gemini من الشريط الجانبي أو عرّف GEMINI_API_KEY في PowerShell.",
    }
}

AGENTS = {
    "chief": ("🧠 Chief Engineer", "Coordinates design, materials, DFM, simulation, and validation."),
    "mechanical": ("🔧 Mechanical Design", "Concepts, mechanisms, loads, sizing, fits, GD&T."),
    "solidworks": ("🧩 SolidWorks CAD", "VBA macros, API automation, drawings, DXF/STEP/BOM."),
    "fea": ("📊 FEA Simulation", "ANSYS/SolidWorks Simulation setup, mesh, BCs, convergence."),
    "cfd": ("🌊 CFD & Thermal", "Fluent/Flow Simulation, domains, y+, turbulence, pressure drop."),
    "manufacturing": ("🏭 Manufacturing DFM/DFA", "Process selection, cost-down, assembly, FMEA."),
    "materials": ("🧪 Materials", "Material selection, substitutions, datasheet interpretation."),
    "patent": ("💡 Invention & Patent", "Novelty, prior art framing, claims, prototype plan."),
}

REFERENCE_BRAIN = {
    "mechanical": ["Shigley’s Mechanical Engineering Design", "Roark’s Formulas for Stress and Strain", "Machinery’s Handbook", "ASME Y14.5 GD&T"],
    "materials": ["Ashby Materials Selection", "ASM Handbook", "MatWeb-style datasheet reasoning", "CES material selection methodology"],
    "manufacturing": ["Kalpakjian Manufacturing Engineering", "SME Manufacturing Engineering Handbook", "Boothroyd Dewhurst DFA logic", "Injection molding and sheet-metal design guides"],
    "fea": ["ANSYS Mechanical Theory Reference", "Practical Finite Element Analysis", "Cook FEA Concepts", "Mesh convergence and verification practices"],
    "cfd": ["Versteeg & Malalasekera CFD", "ANSYS Fluent Theory Guide", "Fox & McDonald Fluid Mechanics", "Incropera Heat Transfer"],
    "solidworks": ["SolidWorks API Help", "VBA macro automation patterns", "Design tables/configurations", "Drawing/BOM automation methods"],
    "patent": ["Patent claim structure", "Prior-art differentiation", "PCT strategy", "Prototype evidence planning"],
}

SYSTEM_BASE = """You are MechAI Pro, a senior mechanical engineering copilot. Answer like a practical expert engineer.
Always structure engineering answers with: assumptions, calculations/checks if relevant, design risks, recommended next action.
Never pretend you performed real FEA/CFD/CAD execution unless the user provided actual solver output or a connected bridge executed it.
Use SI units by default and flag missing inputs.
"""

# ----------------------------- State / Storage -----------------------------
def slugify(name: str) -> str:
    s = re.sub(r"[^\w\-\s]", "", name.strip(), flags=re.UNICODE)
    s = re.sub(r"\s+", "_", s)
    return s[:60] or "Project"

def project_path(name: str) -> Path:
    return PROJECTS_DIR / slugify(name)

def ensure_project(name: str):
    p = project_path(name); p.mkdir(exist_ok=True)
    (p/"files").mkdir(exist_ok=True)
    if not (p/"chat.json").exists(): (p/"chat.json").write_text("[]", encoding="utf-8")
    if not (p/"memory.json").exists(): (p/"memory.json").write_text(json.dumps({"created":datetime.now().isoformat(),"notes":[]}, ensure_ascii=False, indent=2), encoding="utf-8")

def list_projects():
    names = [p.name for p in PROJECTS_DIR.iterdir() if p.is_dir()]
    if not names:
        ensure_project("R&D Lab")
        names = ["R&D_Lab"]
    return sorted(names)

def load_chat(project: str) -> List[Dict]:
    ensure_project(project)
    try: return json.loads((project_path(project)/"chat.json").read_text(encoding="utf-8"))
    except Exception: return []

def save_chat(project: str, messages: List[Dict]):
    ensure_project(project)
    (project_path(project)/"chat.json").write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")

if "lang" not in st.session_state: st.session_state.lang = "English"
if "project" not in st.session_state: st.session_state.project = list_projects()[0]
if "messages" not in st.session_state: st.session_state.messages = load_chat(st.session_state.project)
if "last_agent" not in st.session_state: st.session_state.last_agent = "chief"
if "kb_chunks" not in st.session_state: st.session_state.kb_chunks = []

# ----------------------------- Brain -----------------------------
def route_agent(prompt: str) -> str:
    q = prompt.lower()
    rules = [
        ("solidworks", ["solidworks", "vba", "macro", "swp", "drawing", "bom", "dxf", "step", "cad"]),
        ("cfd", ["cfd", "fluent", "flow simulation", "reynolds", "turbulence", "pressure drop", "y+", "pipe", "fluid", "thermal flow"]),
        ("fea", ["fea", "ansys", "simulation", "static structural", "modal", "buckling", "fatigue", "mesh", "stress analysis"]),
        ("manufacturing", ["dfm", "dfa", "manufacturing", "injection", "molding", "machining", "sheet metal", "cost", "assembly", "fmea"]),
        ("materials", ["material", "polymer", "steel", "aluminum", "stainless", "ashby", "datasheet", "strength", "temperature"]),
        ("patent", ["patent", "claim", "prior art", "novelty", "invention", "pct", "prototype"]),
        ("mechanical", ["shaft", "bearing", "gear", "spring", "mechanism", "tolerance", "gd&t", "load", "torque", "beam"]),
    ]
    for agent, keys in rules:
        if any(k in q for k in keys): return agent
    return "chief"

def extract_pdf_text(file) -> str:
    if PyPDF2 is None: return ""
    reader = PyPDF2.PdfReader(file)
    pages=[]
    for i,p in enumerate(reader.pages[:80]):
        try: pages.append(f"[Page {i+1}]\n" + (p.extract_text() or ""))
        except Exception: pass
    return "\n".join(pages)

def chunk_text(text: str, size=1400, overlap=180):
    chunks=[]; i=0
    while i < len(text):
        chunks.append(text[i:i+size]); i += max(200, size-overlap)
    return chunks

def retrieve_chunks(query: str, chunks: List[str], k=4):
    if not chunks: return []
    terms = set(re.findall(r"\w+", query.lower()))
    scored=[]
    for c in chunks:
        words = set(re.findall(r"\w+", c.lower()))
        scored.append((len(terms & words), c))
    return [c for s,c in sorted(scored, reverse=True)[:k] if s>0]

def local_tool_hint(prompt: str) -> str:
    q = prompt.lower()
    # Simple deterministic calculators if numbers are obvious
    if "reynolds" in q:
        return "Tool available: Reynolds number Re = rho*V*D/mu. Ask for rho, velocity, diameter, viscosity if missing."
    if "pressure drop" in q:
        return "Tool available: Darcy-Weisbach ΔP = f*(L/D)*(rho*V²/2). Need pipe length, diameter, velocity/flow, density, viscosity, roughness."
    if "beam" in q:
        return "Tool available: simply supported center load: Mmax=P*L/4, sigma=M*c/I, delta=P*L³/(48EI)."
    if "shaft" in q or "torque" in q:
        return "Tool available: circular shaft torsion: tau=16T/(πd³), angle=T*L/(J*G), J=πd⁴/32."
    return ""

def build_prompt(user_prompt: str, agent: str, retrieved: List[str]) -> str:
    refs = REFERENCE_BRAIN.get(agent, []) + REFERENCE_BRAIN.get("mechanical", [])[:2]
    ref_txt = "\n".join([f"- {r}" for r in refs])
    rag_txt = "\n\n".join([f"[PROJECT_REF_{i+1}]\n{c}" for i,c in enumerate(retrieved)])
    tool = local_tool_hint(user_prompt)
    agent_name, agent_desc = AGENTS[agent]
    return f"""{SYSTEM_BASE}
Current specialist: {agent_name} — {agent_desc}
Reference brain to emulate as methodology, not copyrighted text:
{ref_txt}

Project retrieved context:
{rag_txt if rag_txt else 'No uploaded project reference matched this question.'}

Local engineering tool hint:
{tool if tool else 'No deterministic calculator selected.'}

User question:
{user_prompt}
"""

def call_llm(prompt: str, model_id: str, api_key: str) -> str:
    if not api_key:
        return "⚠️ Gemini API key is missing. Add it in the sidebar or set GEMINI_API_KEY in PowerShell."
    if genai is None:
        return "⚠️ google-genai is not installed. Run: pip install google-genai"
    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(model=model_id, contents=prompt)
        return getattr(resp, "text", None) or str(resp)
    except Exception as e:
        return f"⚠️ LLM error: {e}"

# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    st.markdown("""<div class='sidebar-card'><div class='sidebar-title'>⚙️ MechAI Pro</div><div class='sidebar-sub'>Premium mechanical engineering copilot. Chat-first. Project-aware. Agent-routed.</div></div>""", unsafe_allow_html=True)
    lang = st.selectbox("Interface / الواجهة", ["English", "العربية"], index=0 if st.session_state.lang=="English" else 1)
    st.session_state.lang = lang
    tr = T[lang]
    api_key = st.text_input(tr["api"], value=os.getenv("GEMINI_API_KEY", ""), type="password")
    model_id = st.text_input(tr["model"], value="gemini-2.5-flash")
    st.divider()
    st.caption(tr["projects"])
    projects = list_projects()
    selected = st.selectbox("", projects, index=projects.index(st.session_state.project) if st.session_state.project in projects else 0, label_visibility="collapsed")
    if selected != st.session_state.project:
        st.session_state.project = selected
        st.session_state.messages = load_chat(selected)
        st.rerun()
    c1,c2 = st.columns(2)
    with c1:
        if st.button(tr["new_project"], use_container_width=True):
            name = "Project_" + datetime.now().strftime("%Y%m%d_%H%M")
            ensure_project(name); st.session_state.project=name; st.session_state.messages=[]; st.rerun()
    with c2:
        if st.button(tr["save"], use_container_width=True): save_chat(st.session_state.project, st.session_state.messages); st.toast("Saved")
    st.divider()
    st.caption("Agent Brain")
    for k,(n,d) in AGENTS.items():
        active = "border-color:#6EE7F9;" if k == st.session_state.last_agent else ""
        st.markdown(f"<div class='agent-chip' style='{active}'><div class='name'>{n}</div><div class='desc'>{d}</div></div>", unsafe_allow_html=True)
    st.divider()
    with st.expander("📚 Knowledge Vault", expanded=False):
        files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)
        if files and st.button("Index uploaded PDFs", use_container_width=True):
            all_chunks=[]
            for f in files:
                text = extract_pdf_text(f)
                all_chunks.extend(chunk_text(text))
            st.session_state.kb_chunks = all_chunks
            st.success(f"Indexed {len(all_chunks)} chunks")
    with st.expander("🖼️ Vision input", expanded=False):
        st.file_uploader("Attach image", type=["png","jpg","jpeg"], key="vision_file")
    with st.expander("🎙️ Voice input", expanded=False):
        st.audio_input("Record voice", key="voice_file")

tr = T[st.session_state.lang]

# ----------------------------- Main layout -----------------------------
st.markdown(f"""
<div class='hero-mini'>
  <div class='brand'>
    <div class='logo'>⚙</div>
    <div><h1>MechAI Pro</h1><p>{tr['tagline']}</p></div>
  </div>
  <div class='pillrow'>
    <div class='pill'>📁 {st.session_state.project}</div>
    <div class='pill'>🤖 {AGENTS[st.session_state.last_agent][0]}</div>
    <div class='pill'>📚 {len(st.session_state.kb_chunks)} chunks</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Chat-first layout: no right panel before the first message.
if not st.session_state.messages:
    st.markdown(f"""
    <div class='chat-welcome'>
      <h2>{tr['welcome']}</h2>
      <p>{tr['welcome_sub']}</p>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("⌘ Prompt Library / مكتبة الأوامر", expanded=False):
        st.markdown(f"""
        <div class='quick-grid'>
          <div class='quick-card'><b>🔧 Design Review</b><span>Analyze failure modes, mechanism risks, material choices, and validation plan.</span></div>
          <div class='quick-card'><b>📊 FEA Setup</b><span>Build an ANSYS/SolidWorks Simulation plan with loads, mesh, and convergence checks.</span></div>
          <div class='quick-card'><b>🌊 CFD/Thermal</b><span>Create domain, mesh, y+, turbulence model, and validation strategy.</span></div>
          <div class='quick-card'><b>🏭 DFM Cost-down</b><span>Review manufacturability, assembly risk, tolerances, and cost-reduction options.</span></div>
        </div>
        """, unsafe_allow_html=True)
else:
    main, right = st.columns([0.76, 0.24], gap="large")
    with main:
        for m in st.session_state.messages:
            with st.chat_message(m.get("role","assistant")):
                st.markdown(m.get("content",""))
    with right:
        st.markdown("<div class='right-panel'>", unsafe_allow_html=True)
        st.markdown(f"### {tr['right']}")
        st.markdown(f"<div class='kv'><span>{tr['project']}</span><span>{st.session_state.project}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='kv'><span>{tr['agent']}</span><span>{AGENTS[st.session_state.last_agent][0]}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='kv'><span>Knowledge</span><span>{len(st.session_state.kb_chunks)} chunks</span></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander(f"📚 {tr['refs']}", expanded=False):
            refs = REFERENCE_BRAIN.get(st.session_state.last_agent, REFERENCE_BRAIN['mechanical'])[:6]
            for r in refs:
                st.markdown(f"<div class='toolbox'><div class='toolbox-title'>📘 {r}</div><div class='toolbox-text'>Methodology guidance. Upload legal PDFs for exact RAG citations.</div></div>", unsafe_allow_html=True)
        with st.expander(f"🛠️ {tr['tools']}", expanded=True):
            for title, desc in [("Beam / Shaft", "Fast sizing equations and sanity checks."),("FEA / CFD Wizard", "Setup plans, assumptions, mesh strategy."),("DFM / Cost", "Manufacturing risks and cost-down logic.")]:
                st.markdown(f"<div class='toolbox'><div class='toolbox-title'>🛠️ {title}</div><div class='toolbox-text'>{desc}</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------- Chat input -----------------------------
if not api_key:
    st.warning(tr["no_key"])

user_prompt = st.chat_input(tr["input"])
if user_prompt:
    agent = route_agent(user_prompt)
    st.session_state.last_agent = agent
    st.session_state.messages.append({"role":"user", "content":user_prompt, "time":datetime.now().isoformat(), "agent":agent})
    retrieved = retrieve_chunks(user_prompt, st.session_state.kb_chunks, k=4)
    prompt = build_prompt(user_prompt, agent, retrieved)
    answer = call_llm(prompt, model_id, api_key)
    st.session_state.messages.append({"role":"assistant", "content":answer, "time":datetime.now().isoformat(), "agent":agent})
    save_chat(st.session_state.project, st.session_state.messages)
    st.rerun()
