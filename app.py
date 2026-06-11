# -*- coding: utf-8 -*-
"""
MechAI Pro v9 — World-Class Chat UI
Public mechanical engineering AI copilot with OpenAI as primary provider and Gemini as optional backup.
Run: streamlit run app.py
"""
import os, json, re, math
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
# CSS — premium, calm, chat-first, mobile responsive
# -----------------------------------------------------------------------------
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
:root{
  --bg:#060914;
  --panel:#0B1020;
  --panel2:#10182A;
  --panel3:#111B31;
  --line:rgba(148,163,184,.22);
  --line2:rgba(110,231,249,.22);
  --text:#F8FAFC;
  --muted:#9AA8C7;
  --muted2:#71809E;
  --cyan:#6EE7F9;
  --violet:#A78BFA;
  --amber:#FBBF24;
  --green:#22C55E;
  --red:#FB4D63;
  --blue:#60A5FA;
}
html, body, [class*="css"]{font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;}
.stApp{
  color:var(--text);
  background:
    radial-gradient(circle at 15% -10%, rgba(96,165,250,.22), transparent 28%),
    radial-gradient(circle at 85% 0%, rgba(167,139,250,.18), transparent 32%),
    linear-gradient(180deg,#070B16 0%, #050712 100%);
}
#MainMenu, footer, header{visibility:hidden;}
.block-container{max-width:1180px; padding:1.05rem 1.45rem 7.5rem 1.45rem;}
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,rgba(10,15,30,.98),rgba(5,8,18,.98));
  border-right:1px solid var(--line);
  box-shadow:18px 0 60px rgba(0,0,0,.28);
}
[data-testid="stSidebar"] *{color:var(--text);} 
[data-testid="stSidebar"] .stButton button{
  border-radius:16px; border:1px solid rgba(96,165,250,.28); background:rgba(17,24,39,.82); color:#fff;
  height:46px; font-weight:700;
}
[data-testid="stSidebar"] .stButton button:hover{border-color:rgba(110,231,249,.55); background:rgba(30,41,59,.92);}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stTextInput"] input{
  background:rgba(10,14,26,.92) !important; border:1px solid rgba(148,163,184,.16) !important; border-radius:14px !important;
}
[data-testid="stExpander"]{
  background:rgba(8,12,24,.72); border:1px solid var(--line) !important; border-radius:18px !important; overflow:hidden;
}
.sidebar-card{
  border:1px solid rgba(110,231,249,.18);
  background:linear-gradient(135deg,rgba(20,28,50,.92),rgba(10,15,30,.92));
  border-radius:24px; padding:22px 20px; margin:10px 0 24px;
  box-shadow:0 20px 70px rgba(0,0,0,.25);
}
.sidebar-card h2{font-size:24px; margin:0 0 8px; letter-spacing:-.05em;}
.sidebar-card p{font-size:13px; color:#B6C5E5; line-height:1.65; margin:0;}
.status-ok{color:var(--green); font-weight:800; margin:8px 0 4px;}
.status-warn{color:var(--amber); font-weight:800; margin:8px 0 4px;}
.topbar{
  position:relative; overflow:hidden;
  border:1px solid rgba(110,231,249,.20);
  background:linear-gradient(135deg,rgba(16,24,43,.94),rgba(8,13,24,.90));
  border-radius:28px; padding:18px 20px; margin:6px 0 18px;
  box-shadow:0 24px 90px rgba(0,0,0,.30);
}
.topbar:before{
  content:""; position:absolute; inset:-2px; pointer-events:none;
  background:radial-gradient(circle at 4% 10%,rgba(110,231,249,.20),transparent 22%),radial-gradient(circle at 88% 0%,rgba(167,139,250,.18),transparent 24%);
}
.topbar-inner{position:relative; display:flex; justify-content:space-between; align-items:center; gap:18px;}
.brandbox{display:flex; align-items:center; gap:14px; min-width:0;}
.logo-orb{
  width:54px;height:54px;border-radius:18px;display:grid;place-items:center;font-size:27px;font-weight:900;color:#06101B;
  background:linear-gradient(135deg,#6EE7F9 0%,#A78BFA 100%); box-shadow:0 0 34px rgba(110,231,249,.25);
}
.brandbox h1{font-size:30px; margin:0; letter-spacing:-.06em; line-height:1;}
.brandbox p{font-size:13px; color:#B8C7EA; margin:7px 0 0;}
.badges{display:flex; flex-wrap:wrap; justify-content:flex-end; gap:8px;}
.badge{
  border:1px solid rgba(148,163,184,.25); background:rgba(15,23,42,.66); border-radius:999px;
  padding:9px 13px; font-size:12px; color:#DDE7FF; font-weight:700; white-space:nowrap;
}
.notice{
  border:1px solid rgba(251,191,36,.36); background:linear-gradient(90deg,rgba(251,191,36,.11),rgba(251,191,36,.045));
  border-radius:18px; padding:12px 16px; color:#FFE9A8; font-size:13px; line-height:1.55; margin:0 0 22px;
}
.hero{
  min-height:44vh; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center;
  padding:18px 0 10px;
}
.hero-kicker{font-size:12px; color:var(--cyan); letter-spacing:.22em; font-weight:900; text-transform:uppercase; margin-bottom:14px;}
.hero h2{font-size:clamp(40px,5vw,76px); line-height:.98; max-width:900px; margin:0; letter-spacing:-.075em; font-weight:900;}
.hero p{max-width:760px; margin:20px auto 22px; color:#B7C7EA; font-size:17px; line-height:1.7;}
.quick-grid{display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; max-width:900px; width:100%; margin-top:8px;}
.quick-chip{
  border:1px solid rgba(148,163,184,.18); background:rgba(15,23,42,.48); border-radius:18px; padding:14px 13px; text-align:left;
  box-shadow:0 18px 40px rgba(0,0,0,.16);
}
.quick-chip b{font-size:13px; display:block; margin-bottom:5px;}
.quick-chip span{font-size:12px; color:#AAB9D7; line-height:1.5;}
.info-strip{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:0 0 18px;}
.info-card{border:1px solid rgba(148,163,184,.16); background:rgba(8,13,25,.55); border-radius:18px; padding:12px 14px;}
.info-card small{display:block;color:#7F8CAB;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.12em;margin-bottom:5px;}
.info-card b{font-size:14px;color:#F8FAFC;}
.message-row{display:flex; gap:13px; margin:22px 0; align-items:flex-start;}
.avatar{width:38px;height:38px;border-radius:14px;display:grid;place-items:center;font-size:19px;flex:0 0 auto;}
.avatar.user{background:linear-gradient(135deg,#FB4D63,#FF8A3D);}
.avatar.ai{background:linear-gradient(135deg,#6EE7F9,#A78BFA); color:#06101B;}
.bubble{max-width:860px; border-radius:22px; padding:16px 18px; line-height:1.72; font-size:15px;}
.bubble.user{background:rgba(251,77,99,.08); border:1px solid rgba(251,77,99,.18);}
.bubble.ai{background:linear-gradient(135deg,rgba(15,23,42,.76),rgba(9,14,26,.70)); border:1px solid rgba(110,231,249,.18); box-shadow:0 18px 48px rgba(0,0,0,.18);}
.bubble p{margin:0 0 .75rem;} .bubble ul,.bubble ol{margin-top:.2rem;} .bubble h1,.bubble h2,.bubble h3{letter-spacing:-.04em;}
.agent-tag{display:inline-flex; gap:6px; align-items:center; padding:5px 9px; border-radius:999px; background:rgba(96,165,250,.10); border:1px solid rgba(96,165,250,.22); color:#C9DCFF; font-size:11px; font-weight:800; margin-bottom:10px;}
.composer-note{position:fixed;left:50%;transform:translateX(-50%);bottom:12px;color:#64748B;font-size:11px;text-align:center;z-index:999;width:100%;pointer-events:none;}
[data-testid="stChatInput"]{background:rgba(5,7,13,.30); backdrop-filter:blur(16px); border-top:1px solid rgba(148,163,184,.10); padding-bottom:16px;}
[data-testid="stChatInput"] textarea{
  border-radius:22px !important; border:1px solid rgba(110,231,249,.28) !important;
  background:rgba(15,23,42,.92) !important; color:#F8FAFC !important; min-height:54px !important;
  box-shadow:0 12px 44px rgba(0,0,0,.28) !important;
}
.footer-line{border-top:1px solid rgba(148,163,184,.14); margin:22px 0 0; padding:18px 0 6px; color:#7785A5; text-align:center; font-size:12px;}
.about-card{border:1px solid rgba(110,231,249,.20);background:rgba(10,15,30,.72);border-radius:24px;padding:24px;line-height:1.75;}
/* Streamlit default content cleanup */
.stMarkdown a{color:#7DD3FC;}
button[kind="secondary"]{border-radius:14px !important;}
@media (max-width: 980px){
  .block-container{padding:0.75rem 0.85rem 7rem;}
  .topbar-inner{align-items:flex-start; flex-direction:column;}
  .badges{justify-content:flex-start;}
  .brandbox h1{font-size:25px;}
  .logo-orb{width:46px;height:46px;border-radius:15px;}
  .quick-grid{grid-template-columns:1fr 1fr;}
  .info-strip{grid-template-columns:1fr;}
  .hero{min-height:42vh; padding-top:12px;}
  .hero h2{font-size:42px;}
  .hero p{font-size:14px;}
  .bubble{max-width:100%; font-size:14px;}
}
@media (max-width: 560px){
  .quick-grid{grid-template-columns:1fr;}
  .hero h2{font-size:34px;}
  .topbar{border-radius:20px;padding:15px;}
  .notice{font-size:12px;}
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Text / Agents / Reference Brain
# -----------------------------------------------------------------------------
TEXT = {
    "English": {
        "input":"Message MechAI Pro…",
        "title":"What would you like to engineer today?",
        "subtitle":"A calm, specialist-routed engineering workspace for design, CAD automation, simulation, CFD, DFM and invention work.",
        "notice":"⚠️ Demo notice: MechAI Pro is an engineering copilot prototype. It does not replace professional engineering verification, certified calculations, CAD/FEA/CFD validation, code compliance, or safety review. Public version is session-only; do not upload confidential files.",
        "about_title":"About MechAI Pro",
        "about":"MechAI Pro is a public mechanical engineering AI copilot demo. It routes questions to specialist engineering agents, uses uploaded references within the current session, and can call OpenAI/ChatGPT as the primary provider with Gemini as backup. Treat all outputs as preliminary engineering assistance and verify them before use.",
        "clear":"Clear chat", "new":"New project", "session":"Session-only public demo. Chats and uploads are not permanently saved.",
        "connected":"connected", "missing":"key missing",
        "prompt_lib":"Prompt Library / مكتبة الأوامر",
        "footer":"MechAI Pro · Public Demo · Mechanical Engineering AI Copilot · Verify all outputs before engineering use",
    },
    "العربية": {
        "input":"اكتب طلبك الهندسي…",
        "title":"ماذا تريد أن تصمم أو تحلل اليوم؟",
        "subtitle":"مساحة عمل هندسية ذكية للتصميم، CAD، المحاكاة، CFD، التصنيع، والاختراع.",
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

# -----------------------------------------------------------------------------
# Brain
# -----------------------------------------------------------------------------
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
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-card">
      <h2>⚙️ MechAI Pro</h2>
      <p>Premium mechanical engineering copilot.<br>Chat-first. Project-aware. Agent-routed.</p>
    </div>
    """, unsafe_allow_html=True)
    lang = st.selectbox("Interface / الواجهة", ["English", "العربية"], index=0 if st.session_state.lang=="English" else 1, label_visibility="visible")
    st.session_state.lang = lang
    tr = TEXT[lang]

    view = st.radio("View", ["Chat", "About"], horizontal=True, index=0 if st.session_state.view=="Chat" else 1)
    st.session_state.view = view

    provider = st.selectbox("AI Provider", ["OpenAI / ChatGPT", "Gemini backup"], index=0 if "OpenAI" in st.session_state.provider else 1)
    st.session_state.provider = provider
    openai_key = get_openai_key(); gemini_key = get_gemini_key()
    if "OpenAI" in provider:
        st.markdown(f"<div class='{ 'status-ok' if openai_key else 'status-warn'}'>● OpenAI {tr['connected'] if openai_key else tr['missing']}</div>", unsafe_allow_html=True)
        model_id = st.text_input("Model", value="gpt-4o-mini", label_visibility="visible")
    else:
        st.markdown(f"<div class='{ 'status-ok' if gemini_key else 'status-warn'}'>● Gemini {tr['connected'] if gemini_key else tr['missing']}</div>", unsafe_allow_html=True)
        model_id = st.text_input("Model", value="gemini-2.5-flash-lite", label_visibility="visible")

    st.divider()
    st.caption("Projects")
    projects = list_projects()
    selected = st.selectbox("Project", projects, index=projects.index(st.session_state.project) if st.session_state.project in projects else 0, label_visibility="collapsed")
    if selected != st.session_state.project:
        st.session_state.project = selected
        st.session_state.messages = load_chat(selected)
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button(tr["new"], use_container_width=True):
            new_name = f"Project_{datetime.now().strftime('%H%M')}"
            if LOCAL_SAVE_ENABLED:
                ensure_project(new_name)
            else:
                st.session_state.project_names.append(new_name)
            st.session_state.project = new_name
            st.session_state.messages = []
            st.rerun()
    with c2:
        if st.button(tr["clear"], use_container_width=True):
            st.session_state.messages = []
            save_chat(st.session_state.project, [])
            st.rerun()

    st.caption("🔒 " + tr["session"])

    with st.expander("Knowledge Vault", expanded=False):
        pdfs = st.file_uploader("Upload PDF references", type=["pdf"], accept_multiple_files=True, label_visibility="visible")
        if pdfs:
            chunks=[]
            for f in pdfs:
                text = extract_pdf_text(f)
                chunks.extend(chunk_text(text))
            st.session_state.kb_chunks = chunks
            st.success(f"Indexed {len(chunks)} chunks for this session.")

    with st.expander("System Health", expanded=False):
        st.write(f"Provider: `{provider}`")
        st.write(f"Project: `{st.session_state.project}`")
        st.write(f"Agent: `{AGENTS.get(st.session_state.last_agent, AGENTS['chief'])[0]}`")
        st.write(f"Knowledge chunks: `{len(st.session_state.kb_chunks)}`")

tr = TEXT[st.session_state.lang]
openai_key = get_openai_key(); gemini_key = get_gemini_key()

# -----------------------------------------------------------------------------
# Main UI
# -----------------------------------------------------------------------------
agent_name = AGENTS.get(st.session_state.last_agent, AGENTS["chief"])[0]
provider_badge = "AI OpenAI" if "OpenAI" in st.session_state.provider else "AI Gemini"

st.markdown(f"""
<div class="topbar">
  <div class="topbar-inner">
    <div class="brandbox">
      <div class="logo-orb">⚙️</div>
      <div><h1>MechAI Pro</h1><p>Mechanical intelligence workspace for R&D, CAD, simulation, CFD, DFM and invention.</p></div>
    </div>
    <div class="badges">
      <div class="badge">📁 {st.session_state.project}</div>
      <div class="badge">{agent_name}</div>
      <div class="badge">{provider_badge}</div>
      <div class="badge">📚 {len(st.session_state.kb_chunks)} chunks</div>
    </div>
  </div>
</div>
<div class="notice">{tr['notice']}</div>
""", unsafe_allow_html=True)

if st.session_state.view == "About":
    st.markdown(f"""
    <div class="about-card">
      <h2>{tr['about_title']}</h2>
      <p>{tr['about']}</p>
      <h3>What this version does</h3>
      <ul>
        <li>Routes engineering prompts to specialist agents.</li>
        <li>Uses OpenAI/ChatGPT as primary provider, with Gemini as optional backup.</li>
        <li>Indexes uploaded PDF references for the current session only.</li>
        <li>Provides safe preliminary reasoning, not certified engineering approval.</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)
else:
    if not st.session_state.messages:
        st.markdown(f"""
        <div class="hero">
          <div class="hero-kicker">AI Mechanical Engineering OS</div>
          <h2>{tr['title']}</h2>
          <p>{tr['subtitle']}</p>
          <div class="quick-grid">
            <div class="quick-chip"><b>🔧 Design Review</b><span>Failure modes, loads, materials and validation.</span></div>
            <div class="quick-chip"><b>📊 FEA Plan</b><span>Loads, fixtures, mesh and convergence strategy.</span></div>
            <div class="quick-chip"><b>🌊 CFD / Thermal</b><span>Flow domain, y+, turbulence and heat transfer.</span></div>
            <div class="quick-chip"><b>🏭 DFM / Cost-down</b><span>Manufacturability, assembly risk and process choice.</span></div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander(tr["prompt_lib"], expanded=False):
            prompts = [
                "Create a short DFM review for an injection molded plastic cover.",
                "Build an ANSYS static structural simulation plan for a bracket loaded by 2 kN.",
                "Generate a SolidWorks VBA macro to export all sheet metal flat patterns to DXF.",
                "Calculate Reynolds number and pressure drop for water flow in a pipe.",
            ]
            for p in prompts:
                if st.button(p, use_container_width=True):
                    st.session_state.pending_prompt = p
                    st.rerun()
    else:
        st.markdown(f"""
        <div class="info-strip">
          <div class="info-card"><small>Routed Agent</small><b>{agent_name}</b></div>
          <div class="info-card"><small>Provider</small><b>{provider_badge}</b></div>
          <div class="info-card"><small>Knowledge</small><b>{len(st.session_state.kb_chunks)} session chunks</b></div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("Engineering Context", expanded=False):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Reference Brain**")
                for r in REFERENCE_BRAIN.get(st.session_state.last_agent, REFERENCE_BRAIN["mechanical"]):
                    st.write("• " + r)
            with col_b:
                st.markdown("**Available tool logic**")
                st.write("• Beam / shaft sanity checks")
                st.write("• Reynolds / pressure-drop equations")
                st.write("• FEA / CFD setup guidance")
                st.write("• DFM/DFA review structure")

        for m in st.session_state.messages:
            role = m.get("role", "assistant")
            content = m.get("content", "")
            a = m.get("agent", "chief")
            if role == "user":
                st.markdown(f"""
                <div class="message-row">
                  <div class="avatar user">☻</div>
                  <div class="bubble user">{content}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                label = AGENTS.get(a, AGENTS["chief"])[0]
                st.markdown(f"""
                <div class="message-row">
                  <div class="avatar ai">⚙️</div>
                  <div class="bubble ai"><div class="agent-tag">{label}</div>
                """, unsafe_allow_html=True)
                st.markdown(content)
                st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown(f"<div class='footer-line'>{tr['footer']}</div>", unsafe_allow_html=True)

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
    with st.spinner("MechAI is engineering the response…"):
        answer = call_llm(prompt, st.session_state.provider, model_id, openai_key, gemini_key)
    st.session_state.messages.append({"role":"assistant", "content":answer, "time":datetime.now().isoformat(), "agent":agent})
    save_chat(st.session_state.project, st.session_state.messages)
    st.rerun()

st.markdown("<div class='composer-note'>MechAI Pro is a demo copilot. Verify calculations, CAD scripts and simulation assumptions before engineering use.</div>", unsafe_allow_html=True)
