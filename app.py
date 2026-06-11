# -*- coding: utf-8 -*-
"""
MechAI Pro v16 — Fixed Sidebar Minimal UI
ChatGPT-like minimal interface with an always-visible fixed sidebar and workspace selector.
Run: streamlit run app.py
"""
import os, json, re, math, html
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from google import genai
except Exception:
    genai = None

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

APP_DIR = Path(__file__).parent
PROJECTS_DIR = APP_DIR / "projects"
LOCAL_SAVE_ENABLED = os.getenv("MECHAI_ENABLE_LOCAL_SAVE", "false").strip().lower() == "true"
if LOCAL_SAVE_ENABLED:
    PROJECTS_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="MechAI Pro",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# CSS — fixed sidebar + near-ChatGPT exact minimal black UI
# -----------------------------------------------------------------------------
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root{
  --bg:#000000;--sidebar:#050505;--surface:#212121;--surface2:#2f2f2f;--hover:#2a2a2a;
  --text:#f4f4f4;--muted:#b4b4b4;--faint:#858585;--line:#242424;--green:#22c55e;--amber:#fbbf24;
}
html,body,[class*="css"]{font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;}
.stApp{background:#000;color:var(--text);}
#MainMenu, footer{visibility:hidden;height:0;}
header[data-testid="stHeader"]{background:transparent!important;height:0!important;visibility:hidden!important;}
[data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"], button[kind="header"]{display:none!important;visibility:hidden!important;opacity:0!important;pointer-events:none!important;}
.block-container{max-width:980px;padding:0 2rem 7.5rem;margin-left:292px!important;}
/* Fixed sidebar: always visible, no collapse behavior */
[data-testid="stSidebar"]{background:#050505!important;border-right:1px solid #1f1f1f!important;min-width:292px!important;max-width:292px!important;width:292px!important;display:block!important;visibility:visible!important;opacity:1!important;position:fixed!important;left:0!important;top:0!important;bottom:0!important;height:100vh!important;transform:translateX(0)!important;z-index:1000!important;overflow-y:auto!important;}
[data-testid="stSidebar"][aria-expanded="false"]{margin-left:0!important;transform:translateX(0)!important;min-width:292px!important;max-width:292px!important;width:292px!important;visibility:visible!important;display:block!important;}
[data-testid="stAppViewContainer"]{margin-left:0!important;}
[data-testid="stMain"]{margin-left:0!important;}
[data-testid="stSidebar"] *{color:var(--text);} 
[data-testid="stSidebar"] section{padding-top:.4rem!important;}
.sidebar-title{font-size:20px;font-weight:700;margin:8px 0 18px;color:#fff;}
.nav-btn{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:10px;color:#f4f4f4;font-size:14px;margin:2px 0;}
.nav-btn.active{background:#2f2f2f;}
.nav-btn:hover{background:#202020;}
.side-label{color:#8f8f8f;font-weight:700;font-size:12px;margin:22px 0 8px;}
.workspace-item{display:flex;gap:10px;align-items:center;color:#f4f4f4;font-size:14px;padding:8px 12px;border-radius:8px;margin:2px 0;}
.workspace-item.active{background:#2f2f2f;}
.workspace-item:hover{background:#202020;}
.project-item{display:flex;gap:10px;align-items:center;color:#f4f4f4;font-size:14px;padding:8px 12px;border-radius:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.project-item:hover{background:#202020;}
.user-chip{position:fixed;bottom:14px;left:12px;width:262px;border-top:1px solid #202020;padding-top:10px;color:#dcdcdc;font-size:13px;}
[data-testid="stSidebar"] .stButton button{width:100%;height:40px;border-radius:10px;border:0;background:#2f2f2f;color:#fff;font-weight:500;text-align:left;}
[data-testid="stSidebar"] .stButton button:hover{background:#3a3a3a;}
[data-testid="stSidebar"] .stRadio > label,[data-testid="stSidebar"] .stSelectbox > label,[data-testid="stSidebar"] .stTextInput > label{color:#8f8f8f!important;font-size:12px!important;font-weight:650!important;}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,[data-testid="stTextInput"] input{background:#111!important;border:1px solid #242424!important;border-radius:10px!important;color:#fff!important;min-height:40px;}
[data-testid="stExpander"]{background:#080808!important;border:1px solid #222!important;border-radius:10px!important;overflow:hidden;}
/* Hide Streamlit cloud chrome/noise */
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton, .viewerBadge_container__1QSob, .viewerBadge_link__1S137 {display:none!important; visibility:hidden!important;}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label{padding:4px 0!important;}
.workspace-select-note{color:#777;font-size:12px;line-height:1.45;margin:6px 0 14px;}

.status-ok{color:var(--green);font-weight:650;font-size:12px;margin:8px 0;}.status-warn{color:var(--amber);font-weight:650;font-size:12px;margin:8px 0;}
.landing{min-height:72vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;}
.landing h1{font-size:24px;line-height:1.25;font-weight:400;letter-spacing:-.015em;margin:0 0 36px;color:#f4f4f4;}
.message-row{display:flex;gap:16px;margin:26px auto;align-items:flex-start;max-width:820px;}
.avatar{width:32px;height:32px;border-radius:50%;display:grid;place-items:center;font-size:14px;flex:0 0 auto;}
.avatar.user{background:#7c3aed;color:#fff;}.avatar.ai{background:#1f1f1f;color:#f1f1f1;border:1px solid #333;}
.bubble{max-width:760px;line-height:1.75;font-size:15px;color:#f3f3f3;}.bubble.user{padding-top:5px;font-weight:500;}.bubble.ai{padding-top:2px;}
.agent-tag{display:inline-flex;color:#888;font-size:12px;margin-bottom:8px;}
.about-card{background:transparent;border:0;padding:24px;line-height:1.75;max-width:760px;margin:90px auto 0;color:#e8e8e8;}.about-card h2{font-size:26px;margin-top:0;font-weight:500;}
.footer-line{display:none;}
/* ChatGPT-style fixed composer: full, clean, no tiny input card */
[data-testid="stChatInput"]{
  position:fixed!important;
  left:292px!important;
  right:0!important;
  bottom:0!important;
  width:calc(100vw - 292px)!important;
  background:linear-gradient(180deg,rgba(0,0,0,0),#000 22%,#000 100%)!important;
  padding:22px 24px 28px!important;
  z-index:999!important;
}
[data-testid="stChatInput"] > div{
  width:min(760px, calc(100vw - 340px))!important;
  max-width:760px!important;
  min-width:520px!important;
  margin:0 auto!important;
}
[data-testid="stChatInput"] form,
[data-testid="stChatInput"] div[data-testid="stChatInputContainer"],
[data-testid="stChatInput"] div[data-testid="stChatInputTextArea"]{
  width:100%!important;
  max-width:760px!important;
}
[data-testid="stChatInput"] textarea{
  width:100%!important;
  border-radius:28px!important;
  border:1px solid #3a3a3a!important;
  background:#212121!important;
  color:#fff!important;
  min-height:56px!important;
  box-shadow:none!important;
  padding-left:18px!important;
  font-size:15px!important;
}
[data-testid="stChatInput"] button{background:#f4f4f4!important;color:#000!important;border-radius:999px!important;}
.notice-slim{position:fixed;right:18px;bottom:10px;color:#6f6f6f;font-size:11px;z-index:999;}
.stMarkdown a{color:#d1d5db;}button[kind="secondary"]{border-radius:10px!important;}
@media(max-width:900px){
  /* On small screens keep sidebar visible but narrower, as requested. */
  [data-testid="stSidebar"], [data-testid="stSidebar"][aria-expanded="false"]{min-width:232px!important;max-width:232px!important;width:232px!important;transform:translateX(0)!important;}
  .block-container{padding:0 .9rem 7rem;max-width:100%;margin-left:232px!important;}
  .landing{min-height:68vh;}.landing h1{font-size:22px;margin-bottom:28px;}
  .message-row{gap:10px;margin:20px 0;}.bubble{font-size:14px;max-width:100%;}
  .notice-slim{display:none;}.user-chip{display:none;}
  [data-testid="stChatInput"]{left:232px!important;width:calc(100vw - 232px)!important;padding:16px 14px 22px!important;}
  [data-testid="stChatInput"] > div{width:100%!important;min-width:0!important;max-width:100%!important;}
}
@media(min-width:901px) and (max-width:1180px){
  [data-testid="stChatInput"] > div{width:min(720px, calc(100vw - 320px))!important;min-width:420px!important;}
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Text / Agents / Reference Brain
# -----------------------------------------------------------------------------
TEXT = {
    "English": {
        "input":"Ask anything engineering…",
        "title":"What would you like to engineer today?",
        "subtitle":"Ask once. MechAI routes to the right engineering specialist and builds a structured answer.",
        "notice":"⚠️ Demo notice: MechAI Pro is an engineering copilot prototype. It does not replace professional engineering verification, certified calculations, CAD/FEA/CFD validation, code compliance, or safety review. Public version is session-only; do not upload confidential files.",
        "about_title":"About MechAI Pro",
        "about":"MechAI Pro is a public mechanical engineering AI copilot demo. It routes questions to specialist engineering agents, uses uploaded references within the current session, and can call OpenAI/ChatGPT as the primary provider with Gemini as backup. Treat all outputs as preliminary engineering assistance and verify them before use.",
        "clear":"Clear chat", "new":"New project", "session":"Session-only public demo. Chats and uploads are not permanently saved.",
        "connected":"connected", "missing":"key missing",
        "prompt_lib":"Prompt Library / مكتبة الأوامر",
        "footer":"MechAI Pro · Public Demo · Mechanical Engineering AI Copilot · Verify all outputs before engineering use",
    },
    "العربية": {
        "input":"اسأل أي شيء هندسي…",
        "title":"ماذا تريد أن تصمم أو تحلل اليوم؟",
        "subtitle":"اكتب طلبك مرة واحدة، وسيتم توجيهه للوكيل الهندسي المناسب لإنتاج إجابة منظمة.",
        "notice":"⚠️ تنبيه: MechAI Pro نموذج أولي لمساعد هندسي. لا يغني عن المراجعة الهندسية الاحترافية، الحسابات المعتمدة، تحقق CAD/FEA/CFD، الالتزام بالكود، أو مراجعة السلامة. النسخة العامة مؤقتة؛ لا ترفع ملفات سرية.",
        "about_title":"حول MechAI Pro",
        "about":"MechAI Pro هو نموذج عام لمساعد ذكاء اصطناعي هندسي ميكانيكي. يوجّه الأسئلة لوكلاء متخصصين، ويستخدم المراجع المرفوعة خلال الجلسة الحالية فقط، ويدعم OpenAI/ChatGPT كمزود أساسي مع Gemini كاحتياطي. جميع النتائج مبدئية ويجب التحقق منها هندسيًا قبل الاستخدام.",
        "clear":"مسح المحادثة", "new":"مشروع جديد", "session":"نسخة عامة مؤقتة: لا يتم حفظ المحادثات والملفات بشكل دائم.",
        "connected":"متصل", "missing":"المفتاح غير موجود",
        "prompt_lib":"Prompt Library / مكتبة الأوامر",
        "footer":"MechAI Pro · نسخة عامة · مساعد ذكاء اصطناعي للهندسة الميكانيكية · تحقق من جميع النتائج قبل الاستخدام الهندسي",
    },
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

WORKSPACE_AGENT_HINT = {
    "chief": "Use automatic routing from the user's question.",
    "mechanical": "Bias the answer toward product R&D, mechanisms, sizing, GD&T, and mechanical design decisions.",
    "solidworks": "Bias the answer toward CAD automation, SolidWorks API/VBA, drawings, BOM, DXF/STEP workflows.",
    "fea": "Bias the answer toward ANSYS/SolidWorks Simulation, boundary conditions, mesh, convergence, and result checks.",
    "cfd": "Bias the answer toward CFD, Fluent, Flow Simulation, turbulence, y+, pressure drop, and thermal-fluid validation.",
    "manufacturing": "Bias the answer toward DFM/DFA, process selection, cost-down, FMEA, tooling, assembly, and manufacturing risk.",
    "materials": "Bias the answer toward material selection, substitutions, datasheets, Ashby method, strength, temperature, and cost.",
    "patent": "Bias the answer toward invention analysis, novelty, prototype planning, prior-art thinking, and patent-friendly wording.",
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

# -----------------------------------------------------------------------------
# State / persistence
# -----------------------------------------------------------------------------
def slugify(name: str) -> str:
    s = re.sub(r"[^\w\-\s]", "", name.strip(), flags=re.UNICODE)
    s = re.sub(r"\s+", "_", s)
    return s[:60] or "Project"

def project_path(name: str) -> Path:
    return PROJECTS_DIR / slugify(name)

def ensure_project(name: str):
    if not LOCAL_SAVE_ENABLED:
        return
    p = project_path(name); p.mkdir(exist_ok=True)
    if not (p/"chat.json").exists():
        (p/"chat.json").write_text("[]", encoding="utf-8")

def list_projects():
    if not LOCAL_SAVE_ENABLED:
        return st.session_state.get("project_names", ["RD_Lab"])
    names = [p.name for p in PROJECTS_DIR.iterdir() if p.is_dir()]
    if not names:
        ensure_project("RD_Lab"); names = ["RD_Lab"]
    return sorted(names)

def load_chat(project: str) -> List[Dict]:
    if not LOCAL_SAVE_ENABLED:
        return []
    ensure_project(project)
    try:
        return json.loads((project_path(project)/"chat.json").read_text(encoding="utf-8"))
    except Exception:
        return []

def save_chat(project: str, messages: List[Dict]):
    if not LOCAL_SAVE_ENABLED:
        return
    ensure_project(project)
    (project_path(project)/"chat.json").write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")

def get_secret_key(name: str) -> str:
    try:
        if hasattr(st, "secrets") and name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return os.getenv(name, "").strip()

def get_openai_key() -> str:
    return get_secret_key("OPENAI_API_KEY")

def get_gemini_key() -> str:
    return get_secret_key("GEMINI_API_KEY")

if "lang" not in st.session_state: st.session_state.lang = "English"
if "project_names" not in st.session_state: st.session_state.project_names = ["RD_Lab"]
if "project" not in st.session_state: st.session_state.project = list_projects()[0]
if "messages" not in st.session_state: st.session_state.messages = load_chat(st.session_state.project)
if "last_agent" not in st.session_state: st.session_state.last_agent = "chief"
if "kb_chunks" not in st.session_state: st.session_state.kb_chunks = []
if "view" not in st.session_state: st.session_state.view = "Chat"
if "provider" not in st.session_state: st.session_state.provider = "OpenAI / ChatGPT"
if "workspace" not in st.session_state: st.session_state.workspace = "chief"

# -----------------------------------------------------------------------------
# Brain
# -----------------------------------------------------------------------------
def route_agent(prompt: str) -> str:
    # If the user selected a specific engineering workspace, keep that specialist
    # unless the text clearly asks for another hard domain such as SolidWorks/CFD/etc.
    selected_ws = st.session_state.get("workspace", "chief")
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
    return selected_ws if selected_ws != "chief" else "chief"

def extract_pdf_text(file) -> str:
    if PyPDF2 is None:
        return ""
    reader = PyPDF2.PdfReader(file)
    pages=[]
    for i,p in enumerate(reader.pages[:80]):
        try:
            pages.append(f"[Page {i+1}]\n" + (p.extract_text() or ""))
        except Exception:
            pass
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
Selected workspace: {WORKSPACES.get(st.session_state.get("workspace", "chief"), "General engineering")}
Workspace guidance: {WORKSPACE_AGENT_HINT.get(st.session_state.get("workspace", "chief"), "Use automatic routing.")}
Reference brain to emulate as methodology, not copyrighted text:
{ref_txt}

Project retrieved context:
{rag_txt if rag_txt else 'No uploaded project reference matched this question.'}

Local engineering tool hint:
{tool if tool else 'No deterministic calculator selected.'}

User question:
{user_prompt}
"""

def call_openai(prompt: str, model_id: str, api_key: str) -> str:
    if not api_key:
        return "⚠️ OpenAI API key is missing. Set OPENAI_API_KEY in Streamlit Secrets."
    if OpenAI is None:
        return "⚠️ OpenAI SDK is not installed. Run: pip install openai"
    fallback_models = list(dict.fromkeys([model_id, "gpt-4o-mini", "gpt-4.1-mini"]))
    errors=[]
    client = OpenAI(api_key=api_key)
    for m in fallback_models:
        try:
            resp = client.responses.create(
                model=m,
                instructions="You are MechAI Pro, a practical senior mechanical engineering copilot. Be precise, structured, and conservative about safety-critical claims.",
                input=prompt,
            )
            txt = getattr(resp, "output_text", None) or str(resp)
            if m != model_id:
                return f"_Note: selected OpenAI model was unavailable, so MechAI used `{m}`._\n\n" + txt
            return txt
        except Exception as e:
            errors.append(f"{m}: {e}")
            msg = str(e).lower()
            if not any(x in msg for x in ["503", "unavailable", "overloaded", "rate", "429", "not found", "model", "does not exist", "invalid"]):
                break
    return "⚠️ OpenAI provider failed. Check API billing/quota/key/model access.\n\nDetails:\n" + "\n".join(errors[-3:])

def call_gemini(prompt: str, model_id: str, api_key: str) -> str:
    if not api_key:
        return "⚠️ Gemini API key is missing. Set GEMINI_API_KEY in Streamlit Secrets."
    if genai is None:
        return "⚠️ google-genai is not installed. Run: pip install google-genai"
    fallback_models = list(dict.fromkeys([model_id, "gemini-2.5-flash-lite", "gemini-2.0-flash-lite", "gemini-1.5-flash"]))
    errors=[]
    client = genai.Client(api_key=api_key)
    for m in fallback_models:
        try:
            resp = client.models.generate_content(model=m, contents=prompt)
            txt = getattr(resp, "text", None) or str(resp)
            if m != model_id:
                return f"_Note: selected Gemini model was busy, so MechAI used `{m}`._\n\n" + txt
            return txt
        except Exception as e:
            errors.append(f"{m}: {e}")
            msg = str(e).lower()
            if not any(x in msg for x in ["503", "unavailable", "overloaded", "high demand", "429", "resource_exhausted", "not found", "model"]):
                break
    return "⚠️ Gemini provider failed.\n\nDetails:\n" + "\n".join(errors[-3:])

def call_llm(prompt: str, provider: str, model_id: str, openai_key: str, gemini_key: str) -> str:
    if "Gemini" in provider:
        primary = call_gemini(prompt, model_id, gemini_key)
        if primary.startswith("⚠️") and openai_key:
            return "_Gemini provider failed, so MechAI used OpenAI backup._\n\n" + call_openai(prompt, "gpt-4o-mini", openai_key)
        return primary
    primary = call_openai(prompt, model_id, openai_key)
    if primary.startswith("⚠️") and gemini_key:
        return "_OpenAI provider failed, so MechAI used Gemini backup._\n\n" + call_gemini(prompt, "gemini-2.5-flash-lite", gemini_key)
    return primary

# -----------------------------------------------------------------------------
# Sidebar — ChatGPT-like navigation, minimal
with st.sidebar:
    st.markdown('<div class="sidebar-title">MechAI Pro</div>', unsafe_allow_html=True)

    if st.button("✎  New chat", use_container_width=True):
        st.session_state.messages = []
        save_chat(st.session_state.project, [])
        st.rerun()

    st.markdown('<div class="nav-btn">⌕&nbsp;&nbsp;Search chats</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-btn">▥&nbsp;&nbsp;Library</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-label">Workspace</div>', unsafe_allow_html=True)
    ws_keys = list(WORKSPACES.keys())
    ws_labels = [WORKSPACES[k] for k in ws_keys]
    current_ws = st.session_state.get("workspace", "chief")
    ws_label = st.selectbox("Workspace", ws_labels, index=ws_keys.index(current_ws) if current_ws in ws_keys else 0, label_visibility="collapsed")
    new_ws = ws_keys[ws_labels.index(ws_label)]
    if new_ws != st.session_state.workspace:
        st.session_state.workspace = new_ws
        st.session_state.last_agent = new_ws
        st.rerun()
    st.markdown('<div class="workspace-select-note">Pick a workspace only when you want to bias the answer. MechAI still auto-routes from your question.</div>', unsafe_allow_html=True)

    view = st.radio("", ["Chat", "About"], horizontal=True, index=0 if st.session_state.view=="Chat" else 1, label_visibility="collapsed")
    st.session_state.view = view

    st.markdown('<div class="side-label">Projects</div>', unsafe_allow_html=True)
    projects = list_projects()
    selected = st.selectbox("Project", projects, index=projects.index(st.session_state.project) if st.session_state.project in projects else 0, label_visibility="collapsed")
    if selected != st.session_state.project:
        st.session_state.project = selected
        st.session_state.messages = load_chat(selected)
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("+ Project", use_container_width=True):
            new_name = f"Project_{datetime.now().strftime('%H%M')}"
            if LOCAL_SAVE_ENABLED:
                ensure_project(new_name)
            else:
                st.session_state.project_names.append(new_name)
            st.session_state.project = new_name
            st.session_state.messages = []
            st.rerun()
    with c2:
        if st.button("Clear", use_container_width=True):
            st.session_state.messages = []
            save_chat(st.session_state.project, [])
            st.rerun()

    # Quiet settings: hidden by default to avoid visual noise.
    with st.expander("Settings", expanded=False):
        lang = st.selectbox("Interface / الواجهة", ["English", "العربية"], index=0 if st.session_state.lang=="English" else 1)
        st.session_state.lang = lang
        provider = st.selectbox("AI", ["OpenAI / ChatGPT", "Gemini backup"], index=0 if "OpenAI" in st.session_state.provider else 1)
        st.session_state.provider = provider
        openai_key = get_openai_key(); gemini_key = get_gemini_key()
        if "OpenAI" in provider:
            st.markdown(f"<div class='{ 'status-ok' if openai_key else 'status-warn'}'>● OpenAI {TEXT[st.session_state.lang]['connected'] if openai_key else TEXT[st.session_state.lang]['missing']}</div>", unsafe_allow_html=True)
            model_id = st.text_input("Model", value="gpt-4o-mini")
        else:
            st.markdown(f"<div class='{ 'status-ok' if gemini_key else 'status-warn'}'>● Gemini {TEXT[st.session_state.lang]['connected'] if gemini_key else TEXT[st.session_state.lang]['missing']}</div>", unsafe_allow_html=True)
            model_id = st.text_input("Model", value="gemini-2.5-flash-lite")
        pdfs = st.file_uploader("Upload PDF references", type=["pdf"], accept_multiple_files=True)
        if pdfs:
            chunks=[]
            for f in pdfs:
                text = extract_pdf_text(f)
                chunks.extend(chunk_text(text))
            st.session_state.kb_chunks = chunks
            st.success(f"Indexed {len(chunks)} chunks for this session.")

    st.markdown('<div class="user-chip">Wafeeq · MechAI Pro</div>', unsafe_allow_html=True)

tr = TEXT[st.session_state.lang]
openai_key = get_openai_key(); gemini_key = get_gemini_key()
agent_name = AGENTS.get(st.session_state.last_agent, AGENTS["chief"])[0]
provider_badge = "OpenAI" if "OpenAI" in st.session_state.provider else "Gemini"

# -----------------------------------------------------------------------------
# Main UI — minimal ChatGPT-style center
# No header, no top badges, no dashboard. The conversation is the product.

if st.session_state.view == "About":
    st.markdown(f"""
    <div class="about-card">
      <h2>{html.escape(tr['about_title'])}</h2>
      <p>{html.escape(tr['about'])}</p>
      <div class="thin-divider"></div>
      <p><b>Public demo notice:</b> MechAI Pro does not replace professional engineering verification, certified calculations, CAD/FEA/CFD validation, code compliance, or safety review. Do not upload confidential files to the public version.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    if not st.session_state.messages:
        greeting = "Good to see you, Wafeeq." if st.session_state.lang == "English" else "أهلًا وفيق."
        st.markdown(f"""
        <div class="landing">
          <h1>{greeting}</h1>
        </div>
        """, unsafe_allow_html=True)
    else:
        for m in st.session_state.messages:
            role = m.get("role", "assistant")
            content = m.get("content", "")
            a = m.get("agent", "chief")
            if role == "user":
                st.markdown(f"""
                <div class="message-row">
                  <div class="avatar user">☻</div>
                  <div class="bubble user">{html.escape(content)}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                label = AGENTS.get(a, AGENTS["chief"])[0]
                st.markdown(f"""
                <div class="message-row">
                  <div class="avatar ai">⚙</div>
                  <div class="bubble ai"><div class="agent-tag">{html.escape(label)} · {html.escape(provider_badge)}</div>
                """, unsafe_allow_html=True)
                st.markdown(content)
                st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown(f"<div class='notice-slim'>{html.escape(tr['footer'])}</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Chat input and execution
# -----------------------------------------------------------------------------
pending = st.session_state.pop("pending_prompt", None) if "pending_prompt" in st.session_state else None
user_prompt = pending or st.chat_input(tr["input"])

if user_prompt:
    agent = route_agent(user_prompt)
    st.session_state.last_agent = agent
    retrieved = retrieve_chunks(user_prompt, st.session_state.kb_chunks)
    prompt = build_prompt(user_prompt, agent, retrieved)
    st.session_state.messages.append({"role":"user", "content":user_prompt, "time":datetime.now().isoformat(), "agent":agent})
    with st.spinner("Thinking…"):
        answer = call_llm(prompt, st.session_state.provider, model_id, openai_key, gemini_key)
    st.session_state.messages.append({"role":"assistant", "content":answer, "time":datetime.now().isoformat(), "agent":agent})
    save_chat(st.session_state.project, st.session_state.messages)
    st.rerun()
