# -*- coding: utf-8 -*-
"""
MechAI Pro v24 — Mechanical Engineering OS Foundation
- Knowledge-first, internal-only build.
- Implements points 6-10 in one integrated release:
  6) Legal reference ingestion and internal reference library
  7) Real project memory
  8) SolidWorks / CAD bridge foundation
  9) FEA / CFD simulation brain foundation
  10) Professional report/export outputs
Run: streamlit run app.py
"""
from __future__ import annotations

import csv
import html
import io
import json
import math
import os
import re
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import streamlit as st

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None

try:
    from docx import Document
except Exception:  # pragma: no cover
    Document = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
except Exception:  # pragma: no cover
    SimpleDocTemplate = Paragraph = Spacer = getSampleStyleSheet = A4 = None

try:
    from openpyxl import Workbook
except Exception:  # pragma: no cover
    Workbook = None

APP_DIR = Path(__file__).parent
KNOWLEDGE_DIR = APP_DIR / "knowledge_packs"
PROJECT_DIR = APP_DIR / "project_memory"
BUILD_ID = "V24_ENGINEERING_OS_FOUNDATION_2026_06_13"

WORKSPACES = {
    "chief": "🧠 General engineering",
    "mechanical": "🔧 Mechanical Design",
    "solidworks": "🧩 CAD / SolidWorks",
    "fea": "📊 Simulation / FEA",
    "cfd": "🌊 CFD / Thermal",
    "manufacturing": "🏭 Manufacturing / DFM",
    "materials": "🧪 Materials Selection",
    "patent": "💡 Innovation / Patent",
}

AGENTS = {
    "chief": "🧠 Chief Mechanical Scientist",
    "mechanical": "🔧 Mechanical Design Scientist",
    "solidworks": "🧩 CAD / SolidWorks Automation Scientist",
    "fea": "📊 FEA Simulation Scientist",
    "cfd": "🌊 CFD / Thermal Scientist",
    "manufacturing": "🏭 Manufacturing DFM/DFA Scientist",
    "materials": "🧪 Materials Selection Scientist",
    "patent": "💡 Innovation / Patent Scientist",
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
    "project_reference": "Project Reference",
}

INTENT_KEYWORDS = {
    "mechanical": ["shaft", "bearing", "spring", "gear", "beam", "fatigue", "stress", "bolt", "fastener", "deflection", "tolerance", "gd&t", "fit", "load"],
    "solidworks": ["solidworks", "macro", "vba", "api", "sldprt", "drawing", "bom", "dxf", "step", "sketch", "feature", "cad", "part", "assembly"],
    "fea": ["fea", "ansys", "static", "modal", "buckling", "mesh", "contact", "boundary", "finite element", "convergence", "element", "load case"],
    "cfd": ["cfd", "fluent", "flow", "thermal", "heat", "reynolds", "pressure drop", "turbulence", "y+", "convection", "pipe", "duct", "cooling"],
    "manufacturing": ["dfm", "dfa", "manufacturing", "injection", "molding", "moulding", "machining", "sheet metal", "tooling", "draft", "sink", "warpage", "boss", "rib", "cycle time", "assembly", "cost"],
    "materials": ["material", "materials", "abs", "pc", "pp", "pa", "nylon", "peek", "steel", "aluminum", "elastomer", "corrosion", "ashby", "datasheet", "stiffness", "strength"],
    "patent": ["patent", "claim", "prior art", "novelty", "invention", "innovation", "prototype", "triz", "wipo", "uspto"],
}

QUERY_EXPANSIONS = {
    "cover": ["enclosure", "lid", "housing", "wall thickness", "rib", "boss", "snap", "cosmetic"],
    "injection": ["molding", "draft", "tooling", "gate", "ejector", "shrinkage", "warpage", "sink", "rib", "boss", "thermoplastic"],
    "shaft": ["torsion", "fatigue", "keyway", "bearing seat", "critical speed"],
    "beam": ["bending", "deflection", "moment", "span", "support"],
    "fea": ["mesh", "contact", "convergence", "constraints", "loads", "validation"],
    "cfd": ["reynolds", "turbulence", "pressure drop", "y plus", "mesh", "boundary", "convergence"],
    "solidworks": ["macro", "vba", "api", "drawing", "bom", "dxf", "step"],
    "material": ["strength", "stiffness", "toughness", "temperature", "corrosion", "process", "cost"],
}

PROTOCOLS = {
    "chief": [
        "Define objective, decision, acceptance criteria, and domain boundaries.",
        "Route to the strongest workspace, then cross-check adjacent domains.",
        "Retrieve internal references and project memory before any recommendation.",
        "State assumptions, missing data, confidence, and verification requirements.",
    ],
    "manufacturing": [
        "Identify process family, material family, production volume, and surface/function requirements.",
        "Map geometry to process capability, tooling, cycle time, and defect modes.",
        "Score risks for wall thickness, draft, ribs/bosses, tooling, tolerance, assembly, quality, and cost.",
        "Rank corrective actions by risk reduction, cost impact, and ease of implementation.",
    ],
    "mechanical": [
        "Define function, loads, supports, geometry, material, life, and environment.",
        "Check yield, fatigue, deflection, buckling, wear, fasteners, fits, and validation.",
        "Use deterministic calculations before relying on CAD/FEA detail.",
        "Link final recommendations to safety factor, test plan, and manufacturability.",
    ],
    "materials": [
        "Translate function into material requirements and constraints.",
        "Compare stiffness, strength, toughness, density, thermal range, chemical resistance, process compatibility, availability, and cost.",
        "Reject materials that fail environment, manufacturing, regulatory, or supply constraints.",
        "Require grade-specific datasheet confirmation before release.",
    ],
    "solidworks": [
        "Clarify document type, units, target geometry, output files, naming, and overwrite policy.",
        "Separate geometry creation, feature creation, drawing, BOM, export, and validation.",
        "Generate clean macro structure with error handling and user-visible run instructions.",
        "Validate destructive operations and file paths before execution.",
    ],
    "fea": [
        "Define simulation objective, physics, acceptance criterion, and decision supported.",
        "Check loads, constraints, contacts, material model, element type, mesh, and convergence.",
        "Plan validation using hand calculation, benchmark, or test evidence.",
        "Interpret plots only after assumptions, boundary conditions, and convergence are verified.",
    ],
    "cfd": [
        "Define domain, objective, fluid properties, heat sources, and boundary conditions.",
        "Estimate Reynolds number and choose laminar/turbulence model and wall treatment.",
        "Check mesh, y+, convergence, conservation balances, and sensitivity.",
        "Validate with pressure-drop, heat-transfer, or experimental estimates.",
    ],
    "patent": [
        "Separate problem, inventive concept, implementation, and measurable advantage.",
        "Map prior-art search keywords, classifications, and closest alternatives.",
        "Convert idea into prototype requirements and claim-like elements.",
        "Avoid legal certainty without patent attorney review.",
    ],
}

SEED_KNOWLEDGE: Dict[str, Dict[str, str]] = {
    "manufacturing_dfm": {
        "injection_molding_expert.md": """# Injection Molding Expert Pack
Concept: Injection molding couples part geometry, thermoplastic behavior, tooling, cooling, ejection, surface class, dimensional capability, and production volume.
Decision logic:
- Use injection molding when production volume and geometry justify tooling cost.
- Treat material grade, nominal wall thickness, draft, rib/boss design, gate/ejector/parting-line plan, shrinkage, and cosmetic surfaces as release-critical.
Rules:
- Keep wall thickness uniform; avoid thick masses and abrupt transitions.
- Add draft to pull-direction walls, ribs, and bosses; textured surfaces require more draft.
- Use ribs for stiffness; avoid thick rib roots that create sink.
- Core bosses and support them with ribs; avoid isolated thick bosses.
- Protect cosmetic A-surfaces from gate marks, ejector marks, weld lines, and parting line mismatch.
Inputs required: CAD/STEP/image, material grade, nominal wall thickness, surface class, annual volume, assembly method, critical dimensions, tolerance requirements, operating environment.
Failure modes: sink marks, voids, short shots, weld line weakness, warpage, shrinkage variation, flash, ejection damage, brittle snaps, dimensional drift, high cycle time.
""",
        "sheet_metal_expert.md": """# Sheet Metal Expert Pack
Decision logic:
- Match thickness, bend radius, tooling, alloy ductility, surface direction, and flat pattern requirements.
Rules:
- Keep holes and slots away from bend lines; add bend relief when tearing or bulging is likely.
- Minimize bend setups and forming directions.
- Define grain direction, K-factor, bend radius, burr direction, finish side, and inspection datums.
Risks: cracking, springback, distortion, burrs, poor flatness, handling marks, tolerance stack-up.
""",
        "machining_expert.md": """# Machining Expert Pack
Decision logic:
- Cost is driven by setup count, tool access, material machinability, tolerance, surface finish, inspection, and deburring.
Rules:
- Reduce deep pockets, long-reach tools, thin walls, sharp internal corners, and unnecessary tight tolerances.
- Prefer standard cutter sizes, standard holes, accessible features, stable datums, and realistic fixturing.
- Separate prototype-friendly geometry from production-stable geometry.
""",
        "assembly_dfa_expert.md": """# Assembly DFA Expert Pack
Decision logic:
- Assembly cost and quality depend on part count, fasteners, orientation, access, mistake-proofing, and inspection.
Rules:
- Reduce part count and fastener count where function allows.
- Use self-locating, self-aligning, and poka-yoke features.
- Keep assembly directions simple and visible.
Risks: wrong orientation, hidden fasteners, poor access, tolerance buildup, rework, long takt time.
""",
        "tolerance_capability_expert.md": """# Tolerance Capability Expert Pack
Decision logic:
- A tolerance is feasible only if process capability, datums, measurement method, and environmental effects support it.
Rules:
- Avoid tight tolerances unless tied to function.
- Use GD&T datums that match manufacturing and inspection.
- Ask for Cpk/PPAP/inspection method when tolerances are release-critical.
Risks: high scrap, rework, measurement disagreement, supplier variation, assembly failure.
""",
        "cost_reduction_expert.md": """# Cost Reduction Expert Pack
Decision logic:
- Reduce cost by removing complexity that does not support function or quality.
Rules:
- Target material usage, cycle time, setup count, tooling complexity, secondary operations, inspection burden, scrap, and assembly time.
- Rank actions by cost impact, risk, implementation effort, and validation effort.
""",
        "quality_control_expert.md": """# Quality Control Expert Pack
Decision logic:
- Quality plan must convert design risks into measurable controls.
Rules:
- Identify CTQs, inspection method, sampling plan, capability target, and defect containment.
- For injection molding, monitor dimensions, sink/warpage, short shots, flash, color, surface defects, and assembly fit.
""",
    },
    "mechanical_design": {
        "shafts.md": """# Shafts
Use combined torsion, bending, fatigue, stress concentration, keyway effects, bearing seats, deflection, and critical speed checks. Required inputs: torque, speed, span, loads, material, keyway, diameter, life, safety factor.
""",
        "beams.md": """# Beams
Check support condition, span, load type, section modulus, bending stress, shear, deflection, and safety factor. Use hand calculation before FEA.
""",
        "bearings.md": """# Bearings
Select bearings from load, speed, life, lubrication, contamination, temperature, alignment, and mounting constraints. Use L10 life as a first sizing check, not final approval.
""",
        "gears.md": """# Gears
Evaluate ratio, torque, face width, module/DP, contact stress, bending stress, lubrication, noise, backlash, material, heat treatment, and manufacturing quality.
""",
        "springs.md": """# Springs
Check load-deflection curve, solid height, stress, fatigue, buckling, material, temperature, relaxation, and manufacturability.
""",
        "fasteners.md": """# Fasteners
Check preload, joint stiffness, thread engagement, fatigue, loosening, torque scatter, corrosion, access, and serviceability.
""",
        "fatigue.md": """# Fatigue
Fatigue evaluation needs stress amplitude, mean stress, surface finish, size, reliability, notch effects, environment, and load spectrum. Do not use static safety factor as fatigue approval.
""",
        "gdnt_tolerances.md": """# GD&T and Tolerances
Datums must reflect function, manufacturing, and inspection. Use GD&T to control functional relationships, not to decorate drawings. Avoid unnecessary tight limits.
""",
    },
    "simulation_fea": {
        "static_structural.md": """# Static Structural FEA
Define objective, loads, constraints, contacts, material model, element type, mesh strategy, convergence metric, and validation method.
""",
        "modal_analysis.md": """# Modal Analysis
Define boundary condition realism, mass participation, mode shapes, operating excitation, and correlation with test when possible.
""",
        "buckling.md": """# Buckling
Distinguish eigenvalue buckling from nonlinear imperfection-sensitive buckling. Validate load paths and initial imperfections.
""",
        "fatigue_fea.md": """# Fatigue FEA
Fatigue requires load history, mean stress correction, material S-N data, notch effects, surface finish, and environmental factors.
""",
        "contacts.md": """# Contacts
Contacts require attention to formulation, friction, penetration tolerance, mesh density, convergence, and physical realism.
""",
        "mesh_convergence.md": """# Mesh Convergence
Use mesh refinement studies around stress gradients. Separate singularities from physical stress concentrations.
""",
        "validation.md": """# FEA Validation
Compare with hand calculations, benchmarks, or test evidence. Simulation results are not proof without validation.
""",
    },
    "cfd_thermal": {
        "internal_flow.md": """# Internal Flow
Check Reynolds number, entrance length, roughness, minor losses, pressure drop, turbulence model, wall treatment, and mass conservation.
""",
        "external_flow.md": """# External Flow
Define far-field boundaries, blockage ratio, turbulence intensity, wake resolution, drag/lift metrics, and validation data.
""",
        "reynolds_number.md": """# Reynolds Number
Re = rho * V * D / mu. Use it to classify laminar, transitional, or turbulent flow and to choose modeling assumptions.
""",
        "turbulence_models.md": """# Turbulence Models
Choose model based on boundary layers, separation, swirl, heat transfer, and computational cost. Validate model sensitivity.
""",
        "y_plus.md": """# y Plus
Wall treatment depends on y+. Low-Re resolution and wall functions need different mesh strategies.
""",
        "pressure_drop.md": """# Pressure Drop
Pressure drop depends on friction factor, length, diameter, roughness, velocity, density, and minor losses.
""",
        "heat_transfer.md": """# Heat Transfer
Check conduction, convection, radiation, heat sources, thermal resistance, and uncertainty in heat-transfer coefficients.
""",
    },
    "materials_selection": {
        "thermoplastics.md": """# Thermoplastics
Compare ABS, PP, PC, PA, POM, PEEK, and blends by stiffness, impact, heat deflection, creep, chemical resistance, shrinkage, surface finish, cost, and processability.
""",
        "metals.md": """# Metals
Compare steels, aluminum, stainless, brass, titanium, and cast alloys by strength, stiffness, density, corrosion, machinability, weldability, heat treatment, and cost.
""",
        "elastomers.md": """# Elastomers
Select by hardness, compression set, temperature, chemicals, fatigue, sealing pressure, manufacturing process, and regulatory constraints.
""",
        "corrosion.md": """# Corrosion
Check galvanic pairs, humidity, chemicals, coatings, temperature, crevices, and maintenance conditions.
""",
        "temperature_limits.md": """# Temperature Limits
Temperature affects stiffness, strength, creep, impact, fatigue, dimensional stability, and chemical resistance.
""",
        "ashby_selection_logic.md": """# Ashby Selection Logic
Start with function, constraints, objective, and free variables. Screen by constraints, rank by objective, then verify with datasheets and process capability.
""",
    },
    "cad_solidworks": {
        "macro_generation.md": """# SolidWorks Macro Generation
Use clean VBA structure, explicit units, error handling, object checks, file path validation, rebuild, and user warning before overwrite.
""",
        "drawing_bom_export.md": """# Drawing and BOM Export
Define drawing template, sheet format, views, dimensions, BOM columns, custom properties, revisions, and export paths.
""",
        "feature_strategy.md": """# Feature Strategy
Build parametric, editable features with logical references and stable sketches. Avoid fragile selections where named references are possible.
""",
        "step_dxf_export.md": """# STEP and DXF Export
Validate part state, sheet-metal flat pattern, coordinate system, units, file naming, revision, and export options before release.
""",
    },
    "innovation_patent": {
        "prior_art.md": """# Prior Art
Search by problem, function, mechanism, application, materials, and alternatives. Use multiple keyword families and classifications.
""",
        "claims_thinking.md": """# Claims Thinking
Separate core inventive concept from embodiments. Identify essential features, optional features, and measurable advantage.
""",
        "prototype_validation.md": """# Prototype Validation
Convert inventive claims into testable prototype requirements, failure modes, and commercial validation metrics.
""",
    },
}

@dataclass
class Chunk:
    pack: str
    title: str
    source: str
    text: str
    score: float = 0.0
    confidence: str = "medium"

# =============================================================================
# File and memory utilities
# =============================================================================
def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_\-]+", "_", value.strip())
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "RD_Lab"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_seed_knowledge() -> None:
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    for pack, files in SEED_KNOWLEDGE.items():
        pdir = KNOWLEDGE_DIR / pack
        pdir.mkdir(parents=True, exist_ok=True)
        for filename, content in files.items():
            f = pdir / filename
            if not f.exists() or len(f.read_text(encoding="utf-8", errors="ignore")) < 50:
                f.write_text(content.strip() + "\n", encoding="utf-8")


def get_project_path(project: str) -> Path:
    path = PROJECT_DIR / slugify(project)
    path.mkdir(parents=True, exist_ok=True)
    (path / "uploads").mkdir(exist_ok=True)
    (path / "reports").mkdir(exist_ok=True)
    return path


def default_memory(project: str) -> Dict:
    return {
        "project": project,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "questions": [],
        "decisions": [],
        "assumptions": [],
        "materials": [],
        "calculations": [],
        "uploaded_files": [],
        "generated_reports": [],
        "lessons_learned": [],
        "facts": {},
    }


def load_memory(project: str) -> Dict:
    p = get_project_path(project) / "memory.json"
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return default_memory(project)


def save_memory(memory: Dict) -> None:
    memory["updated_at"] = now_iso()
    try:
        p = get_project_path(memory.get("project", "RD_Lab")) / "memory.json"
        p.write_text(json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def append_unique(memory: Dict, key: str, value: str) -> None:
    value = value.strip()
    if value and value not in memory.setdefault(key, []):
        memory[key].append(value)


def update_memory_from_question(memory: Dict, question: str, workspace: str) -> None:
    memory.setdefault("questions", []).append({"time": now_iso(), "workspace": workspace, "text": question})
    q = question.lower()
    if "abs" in q: append_unique(memory, "materials", "ABS")
    if "polypropylene" in q or " pp" in q: append_unique(memory, "materials", "PP")
    if "pc" in q or "polycarbonate" in q: append_unique(memory, "materials", "PC")
    if "injection" in q: memory.setdefault("facts", {})["process"] = "Injection molding"
    if "sheet metal" in q: memory.setdefault("facts", {})["process"] = "Sheet metal"
    m = re.search(r"(\d+(?:\.\d+)?)\s*mm", q)
    if m:
        memory.setdefault("facts", {})["dimension_mm_detected"] = m.group(1)
    save_memory(memory)

# =============================================================================
# Legal reference ingestion
# =============================================================================
def extract_uploaded_text(uploaded_file) -> Tuple[str, str]:
    name = uploaded_file.name
    suffix = Path(name).suffix.lower()
    raw = uploaded_file.getvalue()
    if suffix == ".pdf":
        if PdfReader is None:
            return "", "PDF extraction unavailable: pypdf is not installed."
        try:
            reader = PdfReader(io.BytesIO(raw))
            pages = []
            for i, page in enumerate(reader.pages[:80]):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(f"\n\n[Page {i+1}]\n{text}")
            return "\n".join(pages).strip(), ""
        except Exception as e:
            return "", f"PDF extraction failed: {e}"
    try:
        return raw.decode("utf-8", errors="ignore"), ""
    except Exception as e:
        return "", f"Text extraction failed: {e}"


def ingest_project_files(project: str, files, memory: Dict) -> List[str]:
    messages = []
    pdir = get_project_path(project)
    for f in files or []:
        safe = slugify(Path(f.name).stem) + Path(f.name).suffix.lower()
        target = pdir / "uploads" / safe
        if target.exists():
            messages.append(f"Already ingested: {f.name}")
            continue
        raw = f.getvalue()
        target.write_bytes(raw)
        text, err = extract_uploaded_text(f)
        txt_path = target.with_suffix(target.suffix + ".txt")
        txt_path.write_text(text or err, encoding="utf-8")
        memory.setdefault("uploaded_files", []).append({
            "time": now_iso(),
            "filename": f.name,
            "stored_as": str(target.relative_to(APP_DIR)),
            "text_file": str(txt_path.relative_to(APP_DIR)),
            "status": "ok" if text else "warning",
            "note": err or "extracted",
        })
        messages.append(f"Ingested: {f.name}" + (f" — {err}" if err else ""))
    save_memory(memory)
    return messages

# =============================================================================
# Retrieval engine
# =============================================================================
def tokenize(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-zA-Z0-9_\+\-\.]+", text.lower()) if len(t) > 1]


def expanded_terms(query: str) -> List[str]:
    terms = tokenize(query)
    extra = []
    q = query.lower()
    for key, values in QUERY_EXPANSIONS.items():
        if key in q:
            extra += tokenize(" ".join(values))
    return sorted(set(terms + extra))


def detect_workspace(query: str, selected_label: str) -> str:
    q = query.lower()
    scores = {k: 0 for k in INTENT_KEYWORDS}
    for ws, keys in INTENT_KEYWORDS.items():
        for kw in keys:
            if kw in q:
                scores[ws] += 1 + (len(kw.split()) * 0.25)
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    for key, label in WORKSPACES.items():
        if label == selected_label:
            return key
    return "chief"


def split_markdown(text: str, max_chars: int = 1200) -> List[str]:
    parts = re.split(r"(?m)^#{1,3}\s+", text)
    chunks = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        while len(part) > max_chars:
            cut = part.rfind(". ", 0, max_chars)
            if cut < 400:
                cut = max_chars
            chunks.append(part[:cut].strip())
            part = part[cut:].strip()
        if part:
            chunks.append(part)
    return chunks


def source_title(path: Path) -> str:
    try:
        rel = path.relative_to(APP_DIR)
    except Exception:
        rel = path
    return str(rel).replace("\\", "/")


def load_knowledge_chunks(project: str) -> List[Chunk]:
    ensure_seed_knowledge()
    chunks: List[Chunk] = []
    for md in KNOWLEDGE_DIR.rglob("*.md"):
        pack = md.parent.name
        text = md.read_text(encoding="utf-8", errors="ignore")
        for part in split_markdown(text):
            chunks.append(Chunk(pack=pack, title=PACK_TITLES.get(pack, pack), source=source_title(md), text=part))
    # Project-specific uploaded references.
    updir = get_project_path(project) / "uploads"
    for txt in updir.glob("*.txt"):
        text = txt.read_text(encoding="utf-8", errors="ignore")
        for part in split_markdown(text):
            chunks.append(Chunk(pack="project_reference", title="Project Reference", source=source_title(txt), text=part, confidence="project"))
    return chunks


def score_chunk(chunk: Chunk, query: str, workspace: str) -> float:
    q_terms = expanded_terms(query)
    text = (chunk.text + " " + chunk.source + " " + chunk.pack).lower()
    score = 0.0
    for t in q_terms:
        if t in text:
            score += 1.0
    pack = WORKSPACE_TO_PACK.get(workspace, "")
    if pack and chunk.pack == pack:
        score *= 1.8
        score += 3.0
    if workspace == "manufacturing" and chunk.pack in {"materials_selection", "cad_solidworks"}:
        score += 1.5
    if workspace == "fea" and chunk.pack == "mechanical_design":
        score += 1.2
    if workspace == "cfd" and chunk.pack in {"materials_selection", "mechanical_design"}:
        score += 0.8
    if chunk.pack == "project_reference":
        score += 2.0
    return score


def retrieve(query: str, workspace: str, project: str, k: int = 6) -> List[Chunk]:
    chunks = load_knowledge_chunks(project)
    for c in chunks:
        c.score = score_chunk(c, query, workspace)
    ranked = sorted([c for c in chunks if c.score > 0], key=lambda c: c.score, reverse=True)
    if not ranked:
        ranked = sorted(chunks, key=lambda c: len(c.text), reverse=True)
    return ranked[:k]

# =============================================================================
# Engineering calculators and validators
# =============================================================================
def risk_label(points: int) -> str:
    if points >= 7: return "High"
    if points >= 4: return "Medium"
    if points >= 1: return "Low"
    return "Unknown"


def extract_numbers(query: str) -> Dict[str, float]:
    q = query.lower()
    values: Dict[str, float] = {}
    patterns = {
        "force_n": r"(?:force|load|p)\s*=?\s*(\d+(?:\.\d+)?)\s*n\b",
        "span_mm": r"(?:span|length|l)\s*=?\s*(\d+(?:\.\d+)?)\s*mm\b",
        "diameter_mm": r"(?:diameter|dia|d)\s*=?\s*(\d+(?:\.\d+)?)\s*mm\b",
        "torque_nm": r"(?:torque|t)\s*=?\s*(\d+(?:\.\d+)?)\s*n\s*m\b",
        "velocity_ms": r"(?:velocity|speed|v)\s*=?\s*(\d+(?:\.\d+)?)\s*m/s\b",
        "density": r"(?:rho|density)\s*=?\s*(\d+(?:\.\d+)?)\b",
        "viscosity": r"(?:mu|viscosity)\s*=?\s*(\d+(?:\.\d+)?)\b",
        "wall_mm": r"(?:wall|thickness)\s*=?\s*(\d+(?:\.\d+)?)\s*mm\b",
        "rib_mm": r"(?:rib)\s*=?\s*(\d+(?:\.\d+)?)\s*mm\b",
        "boss_mm": r"(?:boss)\s*=?\s*(\d+(?:\.\d+)?)\s*mm\b",
    }
    for k, pat in patterns.items():
        m = re.search(pat, q)
        if m:
            values[k] = float(m.group(1))
    return values


def deterministic_checks(query: str) -> Tuple[List[str], List[Dict]]:
    nums = extract_numbers(query)
    notes: List[str] = []
    calcs: List[Dict] = []
    # Reynolds number if enough data.
    if {"density", "velocity_ms", "diameter_mm", "viscosity"}.issubset(nums):
        re_n = nums["density"] * nums["velocity_ms"] * (nums["diameter_mm"] / 1000.0) / nums["viscosity"]
        regime = "laminar" if re_n < 2300 else "transitional" if re_n < 4000 else "turbulent"
        notes.append(f"Reynolds number ≈ {re_n:,.0f}; estimated regime: {regime}.")
        calcs.append({"type": "Reynolds", "result": re_n, "units": "dimensionless", "note": regime})
    # Simple shaft torsion stress.
    if {"torque_nm", "diameter_mm"}.issubset(nums):
        d = nums["diameter_mm"] / 1000.0
        tau = 16 * nums["torque_nm"] / (math.pi * d**3) / 1e6
        notes.append(f"Solid circular shaft torsional shear estimate ≈ {tau:.1f} MPa, before stress concentration/fatigue factors.")
        calcs.append({"type": "Shaft torsion", "result": tau, "units": "MPa", "note": "solid circular shaft estimate"})
    # Beam midspan bending estimate.
    if {"force_n", "span_mm"}.issubset(nums):
        moment = nums["force_n"] * nums["span_mm"] / 4.0
        notes.append(f"Simply supported center-load bending moment estimate: M ≈ {moment:,.1f} N·mm. Need section modulus for stress.")
        calcs.append({"type": "Beam moment", "result": moment, "units": "Nmm", "note": "simple center load"})
    # Injection molding wall/rib/boss sanity.
    if "wall_mm" in nums:
        wall = nums["wall_mm"]
        if wall < 1.0:
            notes.append("Injection molding wall check: wall thickness is very thin; filling, strength, and supplier capability need confirmation.")
        elif wall > 4.0:
            notes.append("Injection molding wall check: wall thickness is thick; sink, voids, cooling time, and warpage risk increase.")
        else:
            notes.append("Injection molding wall check: wall thickness is within a common starting range, but material grade and geometry still control release.")
        calcs.append({"type": "Injection wall sanity", "result": wall, "units": "mm", "note": "preliminary"})
    return notes, calcs

# =============================================================================
# Decision engines
# =============================================================================
def problem_frame(query: str, workspace: str) -> Dict[str, str]:
    q = query.lower()
    frame = {
        "part": "not specified",
        "process": "not specified",
        "material": "not specified",
        "quantities": "not specified",
        "confidence": "Medium",
    }
    if any(w in q for w in ["cover", "lid", "enclosure", "housing"]):
        frame["part"] = "cover/enclosure"
    if "bracket" in q:
        frame["part"] = "bracket"
    if "shaft" in q:
        frame["part"] = "shaft"
    if "injection" in q or "molding" in q:
        frame["process"] = "injection molding"
    elif "sheet metal" in q:
        frame["process"] = "sheet metal"
    elif "machining" in q or "cnc" in q:
        frame["process"] = "machining"
    for mat in ["abs", "pc", "pp", "nylon", "pa", "peek", "steel", "aluminum", "stainless"]:
        if re.search(rf"\b{mat}\b", q):
            frame["material"] = mat.upper()
    if re.search(r"\b\d+\s*(pcs|units|parts|/year|per year|annually)\b", q):
        frame["quantities"] = "specified"
    missing = sum(1 for k in ["part", "process", "material", "quantities"] if frame[k] in ["not specified"])
    frame["confidence"] = "Low-to-medium" if missing >= 2 else "Medium" if missing == 1 else "Higher, pending validation"
    return frame


def dfm_score(query: str, memory: Dict) -> Tuple[int, List[Dict], List[str]]:
    q = query.lower()
    facts = memory.get("facts", {})
    risk_rows = []
    missing = []
    def add(area, risk, reason, action):
        risk_rows.append({"area": area, "risk": risk, "reason": reason, "action": action})
    material_known = any(m.lower() in q for m in ["abs", "pp", "pc", "pa", "nylon", "peek"]) or bool(memory.get("materials"))
    wall_known = bool(re.search(r"(wall|thickness)\s*=?\s*\d", q)) or "wall_mm" in facts
    volume_known = bool(re.search(r"\b\d+\s*(units|pcs|parts|/year|annually)", q))
    cad_known = any(x in q for x in ["cad", "step", "image", "drawing", "geometry"])
    if not material_known:
        add("Material family/grade", "High", "Material controls shrinkage, strength, heat resistance, creep, and tolerances.", "Specify grade or upload datasheet.")
        missing.append("material grade/datasheet")
    if not wall_known:
        add("Wall thickness", "High", "No nominal wall thickness; sink, warpage, filling, and cycle time cannot be judged.", "Provide nominal wall and thick-section locations.")
        missing.append("nominal wall thickness")
    else:
        add("Wall thickness", "Medium", "Wall thickness is mentioned but still needs uniformity and local thick-section review.", "Check ribs/bosses and wall transitions.")
    if "draft" not in q:
        add("Draft", "Medium", "Injection molded vertical walls need draft for tool release.", "Define pull direction and add draft according to material/surface texture.")
        missing.append("draft/pull direction")
    if not cad_known:
        add("Geometry/CAD", "High", "No geometry; ribs, bosses, gates, ejection, parting line, and assembly cannot be validated.", "Upload CAD/STEP/image.")
        missing.append("CAD/STEP/image")
    if not volume_known:
        add("Production volume", "Medium", "Tooling and cavity strategy depend on expected volume.", "Provide annual volume and target cycle time.")
        missing.append("annual production volume")
    add("Ribs and bosses", "High", "Cover parts often need stiffness/mounting; thick bosses cause sink and warpage.", "Core bosses, connect with ribs, avoid thick isolated masses.")
    add("Tolerance feasibility", "Unknown", "Critical dimensions and process capability are not specified.", "List CTQs, datums, inspection method, and capability target.")
    add("Quality control", "Medium", "Cosmetic and dimensional criteria are unknown.", "Define A-surfaces, defect limits, sampling plan, and fit checks.")
    penalty = {"High": 12, "Medium": 7, "Low": 3, "Unknown": 8}
    score = 100 - sum(penalty.get(row["risk"], 5) for row in risk_rows)
    score = max(20, min(95, score))
    return score, risk_rows, missing


def quality_score(workspace: str, query: str, memory: Dict) -> Tuple[str, int, List[Dict], List[str]]:
    if workspace == "manufacturing":
        score, rows, missing = dfm_score(query, memory)
        return "DFM Score", score, rows, missing
    if workspace == "fea":
        rows = [
            {"area": "Objective", "risk": "High" if "objective" not in query.lower() else "Low", "reason": "Simulation purpose must be known.", "action": "Define pass/fail metric."},
            {"area": "Loads", "risk": "High" if "load" not in query.lower() else "Medium", "reason": "Loads define physics and realism.", "action": "Provide magnitude, direction, distribution, and load case."},
            {"area": "Boundary conditions", "risk": "High", "reason": "Constraint realism dominates stress results.", "action": "Define supports/contact/fixtures."},
            {"area": "Mesh convergence", "risk": "Medium", "reason": "No convergence plan.", "action": "Define convergence metric and refinement zones."},
            {"area": "Validation", "risk": "High", "reason": "No hand calculation/test benchmark.", "action": "Add sanity check or benchmark."},
        ]
        return "FEA Setup Quality", 52, rows, ["objective", "loads", "constraints", "material", "mesh convergence", "validation method"]
    if workspace == "cfd":
        rows = [
            {"area": "Flow regime", "risk": "High", "reason": "Reynolds number not defined.", "action": "Provide fluid, velocity/flow rate, diameter/length, viscosity/density."},
            {"area": "Boundary conditions", "risk": "High", "reason": "Inlet/outlet/thermal BCs missing.", "action": "Define pressure/flow/temperature/heat flux."},
            {"area": "Turbulence/y+", "risk": "Medium", "reason": "Wall treatment unknown.", "action": "Set y+ target and turbulence model."},
            {"area": "Convergence", "risk": "Medium", "reason": "Residual and balance targets missing.", "action": "Define residuals and mass/energy imbalance limits."},
        ]
        return "CFD Setup Quality", 50, rows, ["fluid properties", "domain", "flow rate/velocity", "BCs", "mesh/y+", "validation"]
    if workspace == "materials":
        rows = [
            {"area": "Functional requirements", "risk": "High", "reason": "Material selection must start from function.", "action": "Define loads, stiffness, impact, temperature, chemicals, process, cost."},
            {"area": "Process compatibility", "risk": "Medium", "reason": "Manufacturing route controls material options.", "action": "Specify process and supplier constraints."},
            {"area": "Datasheet confirmation", "risk": "High", "reason": "Grade-specific data missing.", "action": "Upload datasheet or define grade."},
        ]
        return "Material Suitability", 55, rows, ["requirements", "environment", "grade", "supplier datasheet"]
    if workspace == "solidworks":
        rows = [
            {"area": "Document target", "risk": "Medium", "reason": "Macro target not fully specified.", "action": "Specify part/assembly/drawing and file paths."},
            {"area": "Overwrite safety", "risk": "High", "reason": "Automation can overwrite files.", "action": "Use explicit output folder and confirmation."},
            {"area": "Validation", "risk": "Medium", "reason": "Rebuild/export checks required.", "action": "Add rebuild status and output existence checks."},
        ]
        return "CAD Automation Risk", 58, rows, ["document type", "output folder", "template", "file naming", "overwrite rule"]
    return "Engineering Readiness", 60, [], ["requirements", "constraints", "validation evidence"]


def ranked_recommendations(workspace: str, rows: List[Dict]) -> List[str]:
    order = {"High": 0, "Unknown": 1, "Medium": 2, "Low": 3}
    sorted_rows = sorted(rows, key=lambda r: order.get(r.get("risk", "Medium"), 2))
    recs = []
    for row in sorted_rows[:6]:
        recs.append(f"{row['area']}: {row['action']}")
    if not recs:
        recs = ["Define requirements, constraints, acceptance criteria, and validation evidence before release."]
    return recs

# =============================================================================
# CAD / Simulation bridge generators
# =============================================================================
def generate_solidworks_macro(task: str) -> str:
    safe_task = task.replace('"', "'")[:180]
    return f"""Option Explicit
' MechAI Pro CAD Bridge — Generated SolidWorks VBA Skeleton
' Task: {safe_task}
' Review before use. This macro is a starting point, not a certified automation release.

Dim swApp As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2

Sub main()
    On Error GoTo EH
    Set swApp = Application.SldWorks
    Set swModel = swApp.ActiveDoc
    If swModel Is Nothing Then
        MsgBox "Open a SolidWorks document before running this macro.", vbExclamation
        Exit Sub
    End If

    ' TODO: Validate document type: swDocPART / swDocASSEMBLY / swDocDRAWING
    ' TODO: Validate units, rebuild status, file path, overwrite policy.
    swModel.ForceRebuild3 False

    MsgBox "MechAI macro skeleton completed. Add task-specific API calls here.", vbInformation
    Exit Sub
EH:
    MsgBox "Macro failed: " & Err.Description, vbCritical
End Sub
"""


def validate_macro(macro: str) -> List[str]:
    checks = []
    if "Option Explicit" not in macro: checks.append("Add Option Explicit.")
    if "Sub main" not in macro: checks.append("Add Sub main entry point.")
    if "On Error" not in macro: checks.append("Add error handling.")
    if "ActiveDoc" not in macro: checks.append("Check active document before modifying files.")
    if not checks:
        checks.append("Macro skeleton passes baseline structure checks. Manual API review still required.")
    return checks


def generate_apdl(task: str) -> str:
    return f"""! MechAI Pro FEA Bridge — ANSYS APDL starter
! Task: {task[:160]}
/prep7
! TODO: Define element type, material, geometry/import, mesh controls.
! et,1,SOLID186
! mp,ex,1,210e9
! mp,prxy,1,0.3
! TODO: Apply boundary conditions and loads.
! TODO: Solve and post-process.
/solu
! solve
finish
/post1
! plnsol,s,eqv
"""


def generate_fluent_journal(task: str) -> str:
    return f"""; MechAI Pro CFD Bridge — Fluent journal starter
; Task: {task[:160]}
; TODO: Read mesh/case
; /file/read-mesh mesh.msh
; TODO: Check mesh quality
; /mesh/check
; TODO: Define models, materials, boundary conditions, residual monitors
; TODO: Initialize and iterate
; /solve/initialize/hyb-initialization
; /solve/iterate 500
"""


def simulation_setup_notes(workspace: str, query: str) -> str:
    if workspace == "fea":
        return """FEA setup package:
- Study type: choose static/modal/buckling/fatigue based on release decision.
- Required: CAD geometry, material model, loads, constraints, contacts, mesh convergence plan, validation method.
- Solver notes: start with hand calculation; run mesh convergence; check singularities and reaction forces.
"""
    if workspace == "cfd":
        return """CFD setup package:
- Required: domain, fluid properties, flow rate/velocity, temperature/heat loads, wall roughness, boundary conditions.
- Solver notes: estimate Reynolds number; choose model/wall treatment; define y+ target; check mass/energy balance.
"""
    return "Simulation setup package requires selecting FEA or CFD workspace."

# =============================================================================
# Answer builder
# =============================================================================
def build_response(query: str, selected_workspace_label: str, project: str, memory: Dict) -> Tuple[str, str, List[Chunk], Dict[str, str]]:
    workspace = detect_workspace(query, selected_workspace_label)
    frame = problem_frame(query, workspace)
    chunks = retrieve(query, workspace, project, k=7)
    score_name, score, risk_rows, missing = quality_score(workspace, query, memory)
    calc_notes, calcs = deterministic_checks(query)
    for calc in calcs:
        memory.setdefault("calculations", []).append({"time": now_iso(), **calc})
    update_memory_from_question(memory, query, workspace)

    protocol = PROTOCOLS.get(workspace, PROTOCOLS["chief"])
    recs = ranked_recommendations(workspace, risk_rows)
    sources = []
    for i, c in enumerate(chunks[:5], start=1):
        sources.append(f"- [K{i}] {c.title} — `{c.source}` — relevance {c.score:.1f}")

    artifacts: Dict[str, str] = {}
    if workspace == "solidworks" or any(x in query.lower() for x in ["macro", "solidworks", "dxf", "step"]):
        artifacts["solidworks_macro.bas"] = generate_solidworks_macro(query)
        artifacts["solidworks_macro_validation.txt"] = "\n".join(validate_macro(artifacts["solidworks_macro.bas"]))
    if workspace == "fea" or "ansys" in query.lower():
        artifacts["ansys_apdl_starter.mac"] = generate_apdl(query)
        artifacts["fea_setup_notes.md"] = simulation_setup_notes("fea", query)
    if workspace == "cfd" or "fluent" in query.lower():
        artifacts["fluent_journal_starter.jou"] = generate_fluent_journal(query)
        artifacts["cfd_setup_notes.md"] = simulation_setup_notes("cfd", query)

    answer = []
    answer.append(f"**Mechanical Engineering OS v24 — {WORKSPACES.get(workspace, workspace)}**")
    answer.append("")
    answer.append("### Problem frame")
    answer.append(f"- Part/component: {frame['part']}.")
    answer.append(f"- Process/physics: {frame['process']}.")
    answer.append(f"- Material: {frame['material']}.")
    answer.append(f"- Quantities: {frame['quantities']}.")
    answer.append(f"- Confidence: {frame['confidence']}.")
    answer.append("")
    answer.append("### Reasoning protocol applied")
    for idx, step in enumerate(protocol, start=1):
        answer.append(f"{idx}. {step}")
    answer.append("")
    answer.append(f"### {score_name}: {score} / 100")
    if risk_rows:
        answer.append("| Area | Risk | Reason | Action |")
        answer.append("|---|---:|---|---|")
        for row in risk_rows:
            answer.append(f"| {row['area']} | {row['risk']} | {row['reason']} | {row['action']} |")
    answer.append("")
    if calc_notes:
        answer.append("### Deterministic checks")
        for note in calc_notes:
            answer.append(f"- {note}")
        answer.append("")
    answer.append("### Missing data required for real release")
    if missing:
        for m in missing[:10]:
            answer.append(f"- {m}")
    else:
        answer.append("- No major missing input detected from text, but release still requires evidence and verification.")
    answer.append("")
    answer.append("### Ranked recommendations")
    for idx, rec in enumerate(recs, start=1):
        answer.append(f"{idx}. {rec}")
    answer.append("")
    if workspace == "manufacturing":
        answer.append("### Manufacturing / DFM decision")
        answer.append("Treat this as a preliminary DFM gate. Do not release tooling until CAD geometry, material grade, wall thickness, draft, ribs/bosses, tolerance CTQs, and inspection plan are confirmed.")
    elif workspace == "fea":
        answer.append("### FEA decision")
        answer.append("Do not treat stress plots as validation until load paths, constraints, contacts, mesh convergence, and hand/test correlation are complete.")
    elif workspace == "cfd":
        answer.append("### CFD decision")
        answer.append("Do not trust CFD visuals until Reynolds regime, boundary conditions, mesh/y+, convergence, and mass/energy balances are verified.")
    elif workspace == "solidworks":
        answer.append("### CAD automation decision")
        answer.append("Generate and review automation in a sandbox copy before running on production CAD files. Validate rebuild, paths, and export outputs.")
    answer.append("")
    answer.append("### Internal sources used")
    answer.extend(sources or ["- No internal source matched strongly. Add legal references or company notes to improve answer quality."])
    answer.append("")
    answer.append("**Engineering use note:** internal guidance only. Validate assumptions, calculations, standards compliance, and test evidence before engineering release.")

    response = "\n".join(answer)
    append_unique(memory, "decisions", f"{score_name}: {score}/100 for latest {WORKSPACES.get(workspace, workspace)} query")
    for m in missing:
        append_unique(memory, "assumptions", f"Missing input: {m}")
    save_memory(memory)
    return response, workspace, chunks, artifacts

# =============================================================================
# Reports and exports
# =============================================================================
def markdown_report(project: str, memory: Dict, messages: List[Dict]) -> str:
    lines = [
        f"# MechAI Pro Engineering Report — {project}",
        "",
        f"Generated: {now_iso()}",
        f"Build: {BUILD_ID}",
        "",
        "## Project memory summary",
        f"- Questions: {len(memory.get('questions', []))}",
        f"- Uploaded files: {len(memory.get('uploaded_files', []))}",
        f"- Decisions: {len(memory.get('decisions', []))}",
        f"- Assumptions/missing inputs: {len(memory.get('assumptions', []))}",
        f"- Calculations: {len(memory.get('calculations', []))}",
        "",
        "## Decisions",
    ]
    for d in memory.get("decisions", [])[-20:]:
        lines.append(f"- {d}")
    lines += ["", "## Assumptions and missing inputs"]
    for a in memory.get("assumptions", [])[-30:]:
        lines.append(f"- {a}")
    lines += ["", "## Materials"]
    for m in memory.get("materials", []):
        lines.append(f"- {m}")
    lines += ["", "## Uploaded references"]
    for f in memory.get("uploaded_files", [])[-20:]:
        lines.append(f"- {f.get('filename')} — {f.get('status')} — {f.get('note')}")
    lines += ["", "## Conversation excerpts"]
    for msg in messages[-12:]:
        role = msg.get("role", "message")
        content = msg.get("content", "")
        lines.append(f"### {role.title()}")
        lines.append(content[:4000])
        lines.append("")
    return "\n".join(lines)


def docx_bytes(md: str) -> bytes:
    if Document is None:
        return md.encode("utf-8")
    doc = Document()
    for line in md.splitlines():
        if line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        elif line.startswith("### "):
            doc.add_heading(line[4:], level=3)
        elif line.startswith("- "):
            doc.add_paragraph(line[2:], style="List Bullet")
        elif line.strip():
            doc.add_paragraph(line)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def pdf_bytes(md: str) -> bytes:
    if SimpleDocTemplate is None:
        return md.encode("utf-8")
    bio = io.BytesIO()
    doc = SimpleDocTemplate(bio, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    for line in md.splitlines():
        line = html.escape(line)
        if not line:
            story.append(Spacer(1, 8)); continue
        if line.startswith("# "):
            story.append(Paragraph(f"<b>{line[2:]}</b>", styles["Title"]))
        elif line.startswith("## "):
            story.append(Paragraph(f"<b>{line[3:]}</b>", styles["Heading2"]))
        elif line.startswith("### "):
            story.append(Paragraph(f"<b>{line[4:]}</b>", styles["Heading3"]))
        else:
            story.append(Paragraph(line, styles["BodyText"]))
        story.append(Spacer(1, 4))
    doc.build(story)
    return bio.getvalue()


def xlsx_bytes(memory: Dict) -> bytes:
    if Workbook is None:
        return json.dumps(memory, indent=2).encode("utf-8")
    wb = Workbook()
    ws = wb.active
    ws.title = "Project Memory"
    ws.append(["Section", "Value"])
    for key in ["project", "created_at", "updated_at"]:
        ws.append([key, memory.get(key, "")])
    sheets = {
        "Questions": memory.get("questions", []),
        "Decisions": memory.get("decisions", []),
        "Assumptions": memory.get("assumptions", []),
        "Materials": memory.get("materials", []),
        "Calculations": memory.get("calculations", []),
        "Uploaded Files": memory.get("uploaded_files", []),
    }
    for title, rows in sheets.items():
        s = wb.create_sheet(title[:31])
        if not rows:
            s.append(["No data"])
            continue
        if isinstance(rows[0], dict):
            headers = sorted({k for row in rows for k in row.keys()})
            s.append(headers)
            for row in rows:
                s.append([row.get(h, "") for h in headers])
        else:
            s.append(["Value"])
            for row in rows:
                s.append([row])
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()

# =============================================================================
# UI
# =============================================================================
def apply_css():
    st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background: #000 !important; color: #f5f5f5; }
[data-testid="stSidebar"] { background: #050505 !important; border-right: 1px solid #242424; min-width: 285px !important; max-width: 330px !important; }
[data-testid="stSidebar"] * { color: #f5f5f5; }
[data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
.block-container { padding-top: 2rem !important; max-width: 980px !important; padding-bottom: 8rem !important; }
.stButton > button { background: #2f2f2f !important; color: #fff !important; border: 0 !important; border-radius: 11px !important; height: 46px; }
.stSelectbox div[data-baseweb="select"] > div { background: #121212 !important; border-color: #333 !important; border-radius: 11px !important; }
.stFileUploader { background: #0b0d14; padding: 0.4rem; border-radius: 12px; }
[data-testid="stChatInput"] { background: #101114 !important; border-top: 0 !important; }
[data-testid="stChatInput"] textarea { background: #212121 !important; border-radius: 24px !important; color: white !important; }
.small-muted { color: #9b9b9b; font-size: 0.88rem; line-height: 1.5; }
.source-chip { background:#101010; border:1px solid #333; border-radius:8px; padding:0.25rem 0.45rem; font-size:0.78rem; }
</style>
""", unsafe_allow_html=True)


def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "project" not in st.session_state:
        st.session_state.project = "RD_Lab"
    if "last_artifacts" not in st.session_state:
        st.session_state.last_artifacts = {}


def sidebar() -> Tuple[str, str, Dict]:
    st.sidebar.markdown("## MechAI Pro")
    if st.sidebar.button("✎ New chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_artifacts = {}
        st.rerun()
    st.sidebar.markdown("⌕ Search chats")
    st.sidebar.markdown("▥ Library")

    st.sidebar.markdown("### Workspace")
    workspace_label = st.sidebar.selectbox("Workspace", list(WORKSPACES.values()), label_visibility="collapsed")
    st.sidebar.markdown('<div class="small-muted">Workspace biases the internal mechanical brain. Auto-routing still reads the question.</div>', unsafe_allow_html=True)

    view = st.sidebar.radio("View", ["Chat", "About"], horizontal=True)

    st.sidebar.markdown("### Projects")
    PROJECT_DIR.mkdir(exist_ok=True)
    existing = sorted([p.name for p in PROJECT_DIR.iterdir() if p.is_dir()]) or ["RD_Lab"]
    if st.session_state.project not in existing:
        existing.insert(0, st.session_state.project)
    project = st.sidebar.selectbox("Project", existing, index=existing.index(st.session_state.project), label_visibility="collapsed")
    st.session_state.project = project
    memory = load_memory(project)
    c1, c2 = st.sidebar.columns(2)
    if c1.button("+ Project", use_container_width=True):
        new = f"Project_{datetime.now().strftime('%H%M%S')}"
        get_project_path(new)
        st.session_state.project = new
        st.session_state.messages = []
        st.rerun()
    if c2.button("Clear", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_artifacts = {}
        st.rerun()

    with st.sidebar.expander("Reference Library / المراجع", expanded=False):
        st.markdown("Only upload documents you are allowed to use. Public hosted storage is demo/session-hosted; do not upload confidential files.")
        files = st.file_uploader("Upload legal references", type=["pdf", "txt", "md", "csv"], accept_multiple_files=True, label_visibility="collapsed")
        if files:
            notes = ingest_project_files(project, files, memory)
            for n in notes:
                st.caption(n)
        st.caption(f"Uploaded references in memory: {len(memory.get('uploaded_files', []))}")

    with st.sidebar.expander("Settings", expanded=False):
        st.markdown("**Mode:** Mechanical Engineering OS — Internal Knowledge First")
        st.markdown("**Build:** " + BUILD_ID)
        st.markdown(f"**Internal docs:** {len(load_knowledge_chunks(project))}")
        st.markdown(f"**Project questions:** {len(memory.get('questions', []))}")
        st.markdown("External AI providers are not the primary reference in this build.")

    st.sidebar.markdown("---")
    st.sidebar.caption("Wafeeq · MechAI Pro")
    return view, workspace_label, memory


def show_about():
    st.markdown("# MechAI Pro")
    st.markdown("""
**Mechanical Engineering Operating System — v24 Foundation**

This build is knowledge-first. It uses internal knowledge packs, project memory, deterministic checks, CAD/simulation bridge templates, and report generation.

Core modules in this build:
- Legal reference ingestion for allowed PDFs/TXT/MD/CSV.
- Project memory for questions, decisions, assumptions, materials, calculations, uploads, reports, and lessons learned.
- SolidWorks/CAD bridge foundation: clean macro generation, baseline validation, `.bas` downloads.
- FEA/CFD simulation brain: setup logic and starter APDL/Fluent scripts.
- Engineering reports: Markdown, Word, PDF, and Excel exports.

Engineering use note: outputs are internal guidance only. Validate calculations, assumptions, standards compliance, and test evidence before engineering release.
""")


def render_messages():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def render_artifacts(memory: Dict):
    artifacts = st.session_state.get("last_artifacts", {}) or {}
    if not artifacts and not st.session_state.messages:
        return
    with st.expander("Engineering outputs / exports", expanded=False):
        if artifacts:
            st.markdown("### Generated technical artifacts")
            for filename, content in artifacts.items():
                mime = "text/plain"
                if filename.endswith(".md"): mime = "text/markdown"
                if filename.endswith(".bas") or filename.endswith(".mac") or filename.endswith(".jou"): mime = "text/plain"
                st.download_button(f"Download {filename}", data=content.encode("utf-8"), file_name=filename, mime=mime, use_container_width=True)
        st.markdown("### Project report")
        md = markdown_report(st.session_state.project, memory, st.session_state.messages)
        c1, c2, c3, c4 = st.columns(4)
        c1.download_button("Markdown", md.encode("utf-8"), file_name=f"{slugify(st.session_state.project)}_report.md", mime="text/markdown", use_container_width=True)
        c2.download_button("Word", docx_bytes(md), file_name=f"{slugify(st.session_state.project)}_report.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        c3.download_button("PDF", pdf_bytes(md), file_name=f"{slugify(st.session_state.project)}_report.pdf", mime="application/pdf", use_container_width=True)
        c4.download_button("Excel", xlsx_bytes(memory), file_name=f"{slugify(st.session_state.project)}_memory.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)


def main():
    st.set_page_config(page_title="MechAI Pro", page_icon="⚙️", layout="wide", initial_sidebar_state="expanded")
    apply_css()
    init_state()
    ensure_seed_knowledge()
    view, workspace_label, memory = sidebar()

    if view == "About":
        show_about()
        return

    if not st.session_state.messages:
        st.markdown("<div style='height: 25vh'></div>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; font-weight:500;'>Good to see you, Wafeeq.</h2>", unsafe_allow_html=True)

    render_messages()
    render_artifacts(memory)

    prompt = st.chat_input("Ask anything engineering...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            answer, routed_workspace, chunks, artifacts = build_response(prompt, workspace_label, st.session_state.project, memory)
            st.markdown(f"<span class='small-muted'>{AGENTS.get(routed_workspace, 'MechAI')} · Internal Knowledge First · Engineering OS v24</span>", unsafe_allow_html=True)
            st.markdown(answer)
            st.session_state.last_artifacts = artifacts
        st.session_state.messages.append({"role": "assistant", "content": answer})
        save_memory(memory)
        st.rerun()

if __name__ == "__main__":
    main()
