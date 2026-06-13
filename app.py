# -*- coding: utf-8 -*-
"""
MechAI Pro v27 — Universal Mechanical Engineering OS
=====================================================
A knowledge-first mechanical engineering operating system foundation.

This build includes the requested v27-v34 capabilities in a single Streamlit app:
- Universal Project System
- Universal Reference Vault
- Engineering Templates Library
- Engineering Report Studio
- Engineering Calculators Pro
- CAD / SolidWorks Automation Studio
- FEA / CFD Simulation Studio
- Account / workspace / permission foundation for multi-tenant evolution

No OpenAI/Gemini dependency. The app uses internal knowledge packs, project memory,
calculators, scoring engines, and deterministic engineering review logic.
"""
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import math
import os
import re
import shutil
import textwrap
import uuid
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import streamlit as st

try:
    import PyPDF2  # type: ignore
except Exception:
    PyPDF2 = None

try:
    from docx import Document  # type: ignore
except Exception:
    Document = None

try:
    from reportlab.lib.pagesizes import A4  # type: ignore
    from reportlab.pdfgen import canvas  # type: ignore
except Exception:
    A4 = None
    canvas = None

try:
    from openpyxl import Workbook  # type: ignore
except Exception:
    Workbook = None

APP_VERSION = "v27_UNIVERSAL_ENGINEERING_OS_2026_06_13"
APP_TITLE = "MechAI Pro"
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "mechai_data"
TENANT_DIR = DATA_DIR / "tenants"
GLOBAL_KNOWLEDGE_DIR = ROOT / "knowledge_packs"
EXPORT_DIR = DATA_DIR / "exports"
for p in [DATA_DIR, TENANT_DIR, GLOBAL_KNOWLEDGE_DIR, EXPORT_DIR]:
    p.mkdir(parents=True, exist_ok=True)

WORKSPACES = {
    "General engineering": {"icon": "🧠", "folder": None, "agent": "Chief Mechanical Engineering Board"},
    "Product R&D / Design": {"icon": "🛠️", "folder": "mechanical_design", "agent": "Mechanical Design Scientist"},
    "CAD / SolidWorks": {"icon": "🧩", "folder": "cad_solidworks", "agent": "CAD / SolidWorks Automation Scientist"},
    "Simulation / FEA": {"icon": "📊", "folder": "simulation_fea", "agent": "FEA Simulation Scientist"},
    "CFD / Thermal": {"icon": "🌊", "folder": "cfd_thermal", "agent": "CFD / Thermal Scientist"},
    "Manufacturing / DFM": {"icon": "🏭", "folder": "manufacturing_dfm", "agent": "Manufacturing DFM/DFA Scientist"},
    "Materials Selection": {"icon": "🧪", "folder": "materials_selection", "agent": "Materials Selection Scientist"},
    "Innovation / Patent": {"icon": "💡", "folder": "innovation_patent", "agent": "Innovation / Patent Scientist"},
}

PROJECT_TYPES = [
    "Product design", "DFM review", "Material selection", "FEA setup", "CFD setup",
    "SolidWorks automation", "Failure analysis", "Cost reduction", "Patent / innovation review",
]

SOURCE_TYPES = [
    "Open reference", "Personal reference", "Project reference", "Team reference",
    "Public datasheet", "Supplier catalog", "Design guide", "Standards summary", "Own engineering note",
]
CONFIDENTIALITY = ["Public", "Internal", "Private", "Confidential"]
ROLES = ["Owner", "Admin", "Engineer", "Reviewer", "Viewer"]

# -----------------------------------------------------------------------------
# Seeded global knowledge library
# -----------------------------------------------------------------------------

KNOWLEDGE_SEED: Dict[str, Dict[str, str]] = {
    "mechanical_design": {
        "beams.md": """
# Beams Expert Pack
Scope: bending, shear, deflection, support conditions, load paths, stiffness and validation.
Required inputs: load case, supports, span, cross-section, material, deflection limit, safety factor.
Core equations: bending stress sigma=M*c/I; simply-supported center load deflection delta=P*L^3/(48*E*I); cantilever end load delta=P*L^3/(3*E*I).
Decision logic: if support or cross-section is missing, do not release sizing; if cyclic loads exist, switch to fatigue reasoning; check stiffness and strength separately.
Failure modes: yielding, excessive deflection, buckling, vibration, local stress concentration, joint failure.
Validation: hand calculation, FEA sanity check, physical load test when critical.
""",
        "shafts.md": """
# Shafts Expert Pack
Scope: torque, bending, fatigue, keyways, bearing seats, critical speed and manufacturability.
Required inputs: torque, speed, bending moment, bearing layout, diameter, material, duty cycle, keyway/spline details.
Equations: solid shaft torsional shear tau=16T/(pi*d^3); angle of twist theta=T*L/(J*G), J=pi*d^4/32.
Decision logic: keyways increase fatigue risk; high speed requires critical speed check; combined bending/torsion requires equivalent stress.
Failure modes: torsional yielding, bending fatigue, fretting, keyway cracking, excessive twist, resonance.
""",
        "bearings.md": """
# Bearings Expert Pack
Scope: bearing selection, L10 life, loads, lubrication, fits, speed and temperature.
Inputs: radial/axial load, speed, life target, type, lubrication, contamination, temperature.
Equation: L10=(C/P)^p million revolutions; p=3 ball bearings, p=10/3 roller bearings; L10h=1e6/(60n)*(C/P)^p.
Decision logic: unknown load spectrum lowers confidence; contamination/lubrication require service factors; rotating ring fit must be checked.
Failures: spalling, overheating, lubrication starvation, contamination wear, brinelling, misalignment.
""",
        "gears.md": """
# Gears Expert Pack
Scope: preliminary gear sizing, ratio, torque, tooth bending, pitting, noise, heat and lubrication.
Inputs: power, speed, ratio, torque, gear type, module/DP, face width, material, heat treatment, duty cycle.
Decision logic: shock load requires service factor; quiet operation may need helical gears; compact gearboxes need thermal check.
Failures: bending fracture, pitting, scuffing, wear, noise, misalignment, lubrication failure.
""",
        "springs.md": """
# Springs Expert Pack
Scope: compression, extension, torsion springs; stiffness, stress, fatigue, buckling, solid height.
Inputs: load range, deflection, envelope, cycle life, temperature, material, end style.
Decision logic: cyclic duty drives fatigue; high temperature drives relaxation risk; slender compression springs may buckle.
Failures: fatigue fracture, coil bind, permanent set, relaxation, buckling, corrosion.
""",
        "fasteners.md": """
# Fasteners Expert Pack
Scope: bolted joints, preload, separation, shear, fatigue, loosening and assembly repeatability.
Inputs: bolt size, grade, clamp length, joint materials, friction, torque method, external loads, vibration.
Core logic: preload is the main design variable; torque-control has high scatter; fatigue risk is reduced by adequate preload and joint stiffness.
Failures: loosening, thread stripping, bolt tensile failure, shear, bearing, fatigue, galvanic corrosion.
""",
        "fatigue.md": """
# Fatigue Expert Pack
Scope: cyclic loads, endurance, mean stress, stress concentration, surface finish and reliability.
Inputs: load spectrum, cycles, material, surface finish, size, temperature, notches, welds.
Decision logic: if load cycles are unknown, fatigue confidence is low; stress concentrations and poor finish reduce life; welds require weld-specific fatigue rules.
Failures: crack initiation at notch/keyway/weld, propagation, sudden fracture.
""",
        "gdnt_tolerances.md": """
# GD&T and Tolerances Expert Pack
Scope: datum strategy, functional tolerancing, tolerance stack-up, process capability and inspection.
Inputs: function, mating parts, datums, CTQ dimensions, manufacturing process, inspection method.
Decision logic: avoid arbitrary tight tolerances; tolerance should follow function and process capability; define datums before feature controls.
Failures: assembly interference, excessive inspection cost, poor repeatability, supplier disputes.
""",
    },
    "manufacturing_dfm": {
        "injection_molding_expert.md": """
# Injection Molding DFM Expert Pack
Scope: thermoplastic part manufacturability, wall thickness, draft, ribs, bosses, sink, warpage, tooling and quality.
Required inputs: material grade, nominal wall thickness, part size, ribs/bosses/snap-fits, surface class, production volume, tolerance targets.
Decision logic: prioritize uniform wall thickness; avoid thick bosses; use ribs for stiffness; add draft for ejection; consider gate, parting line and ejector marks early.
Risk rules: unknown material and wall thickness create high risk; tall ribs and thick bosses increase sink/warpage risk; tight tolerances increase tooling and process risk.
Validation: mold-flow review for critical parts, first article inspection, shrinkage verification, process capability study.
""",
        "sheet_metal_expert.md": """
# Sheet Metal DFM Expert Pack
Scope: bending, bend radius, K-factor, bend allowance, hole-to-bend distance, flat patterns and manufacturability.
Inputs: material, thickness, bend angle, inside radius, tooling, grain direction, tolerances.
Decision logic: inside bend radius should suit material/tooling; holes near bends distort; avoid complex formed features without tooling review.
Validation: flat pattern review, bend sample, tolerance capability check.
""",
        "machining_expert.md": """
# Machining DFM Expert Pack
Scope: CNC milling/turning, setups, tool access, tolerances, surface finish, cycle time and cost.
Inputs: material, geometry, tolerances, finish, volume, datum plan, tool access.
Decision logic: deep pockets, sharp internal corners, tight tolerances and hard materials increase cost; design for fewer setups and standard tools.
Validation: CAM review, setup plan, inspection plan, first article inspection.
""",
        "assembly_dfa_expert.md": """
# Assembly DFA Expert Pack
Scope: part count reduction, orientation, fastening, serviceability, poka-yoke and assembly time.
Inputs: mating parts, assembly sequence, fasteners, access, tools, field service requirements.
Decision logic: reduce part count; avoid ambiguous orientation; design self-locating features; avoid hidden fasteners and fragile assembly steps.
Validation: assembly trial, time study, ergonomic review, error-proofing check.
""",
        "tolerance_capability_expert.md": """
# Tolerance Capability Expert Pack
Scope: process capability, tolerance feasibility, inspection, CTQ dimensions and cost impact.
Inputs: manufacturing process, tolerance values, CTQ list, inspection equipment, supplier capability.
Decision logic: tight tolerances must be justified by function; process capability should be matched to tolerance; unknown CTQ lowers confidence.
Validation: capability study, gauge R&R, first article inspection.
""",
        "cost_reduction_expert.md": """
# Cost Reduction Expert Pack
Scope: material, process, tooling, cycle time, assembly, scrap, inspection and logistics cost drivers.
Inputs: volume, material, process, cycle time, scrap rate, labor content, tooling complexity, supplier constraints.
Decision logic: attack cost through part count reduction, standard materials, process simplification, tolerance relaxation and cycle-time reduction.
""",
        "quality_control_expert.md": """
# Quality Control Expert Pack
Scope: inspection plans, CTQs, failure modes, process capability, first article, sampling and production stability.
Inputs: CTQ dimensions, critical functions, process, volume, inspection method, acceptance criteria.
Decision logic: every high-risk DFM item needs a verification method; inspection should focus on CTQs and failure modes, not every dimension equally.
""",
        "welding.md": """
# Welding DFM Expert Pack
Scope: weld joint design, distortion, access, fixture strategy, inspection and fatigue.
Inputs: material, thickness, joint type, load path, weld process, access, fatigue duty.
Decision logic: design welds for access and inspection; avoid over-welding; account for heat distortion; fatigue welds require special review.
""",
    },
    "materials_selection": {
        "thermoplastics.md": """
# Thermoplastics Materials Expert Pack
Scope: ABS, PC, PP, PA, POM and other plastics for mechanical parts.
Inputs: stiffness, toughness, temperature, chemical exposure, UV, appearance, process, cost, availability.
Decision logic: ABS is common for enclosures; PC improves impact/temperature; PP improves chemical resistance and low cost but lower stiffness; PA absorbs moisture.
Risks: creep, UV degradation, shrinkage, warpage, chemical attack, flammability.
""",
        "metals.md": """
# Metals Materials Expert Pack
Scope: steels, stainless steels, aluminum alloys, brass/bronze and cast alloys.
Inputs: strength, stiffness, corrosion, temperature, weight, manufacturability, surface treatment, cost.
Decision logic: aluminum reduces weight; steels improve strength/cost; stainless improves corrosion; material choice must match manufacturing process.
""",
        "elastomers.md": """
# Elastomers Expert Pack
Scope: rubber-like materials, seals, gaskets, vibration isolation and flexible components.
Inputs: hardness, compression set, temperature, chemicals, UV, seal pressure, fatigue.
Decision logic: select by environment and compression set, not hardness alone.
""",
        "composites.md": """
# Composites Expert Pack
Scope: fiber-reinforced plastics, laminates and anisotropic design logic.
Inputs: load direction, stiffness, manufacturing process, environment, damage tolerance.
Decision logic: align fibers to load paths; validate joints and impact/delamination risks.
""",
        "corrosion.md": """
# Corrosion Expert Pack
Scope: galvanic corrosion, environmental exposure, coatings, stainless/passivation and material compatibility.
Inputs: environment, humidity, chemicals, mating metals, coating, service life.
Decision logic: dissimilar metals require galvanic review; coatings need inspection and damage tolerance.
""",
        "temperature_limits.md": """
# Temperature Limits Expert Pack
Scope: high/low temperature effects, creep, softening, embrittlement and thermal expansion.
Inputs: service temperature, peak temperature, time at temperature, load, material family.
Decision logic: plastics near Tg/heat-deflection limits need creep and deformation review; thermal expansion affects tolerances.
""",
        "ashby_selection_logic.md": """
# Ashby-Style Material Selection Logic
Scope: function-objective-constraints-free variables methodology.
Inputs: function, constraints, objective, free variables, candidate processes.
Decision logic: define requirements before candidates; screen by constraints then rank by objective such as mass/cost/stiffness.
""",
    },
    "simulation_fea": {
        "static_structural.md": """
# Static Structural FEA Expert Pack
Scope: linear/nonlinear static structural setup, loads, supports, contacts, mesh and interpretation.
Inputs: objective, geometry, material, loads, constraints, contacts, failure criteria, validation target.
Decision logic: wrong boundary conditions invalidate results; validate with hand calculation; use mesh convergence; report stress away from singularities.
""",
        "modal_analysis.md": """
# Modal Analysis Expert Pack
Scope: natural frequencies, mode shapes, constraints and resonance risk.
Inputs: mass, stiffness, constraints, operational excitation frequencies.
Decision logic: compare natural frequencies to excitation; verify mass and boundary conditions; do not treat mode shape stress as static stress.
""",
        "buckling.md": """
# Buckling FEA Expert Pack
Scope: linear eigenvalue buckling, nonlinear buckling and slender structures.
Inputs: geometry imperfections, load, supports, material, initial defects.
Decision logic: eigenvalue buckling is optimistic; use nonlinear analysis for critical structures.
""",
        "fatigue_fea.md": """
# Fatigue FEA Expert Pack
Scope: stress-life/strain-life fatigue based on FEA stress results.
Inputs: load cycles, stress history, material fatigue data, surface finish, notch effects.
Decision logic: mesh and stress concentration quality control are critical; mean stress correction may be needed.
""",
        "contacts.md": """
# Contact Modeling Expert Pack
Scope: bonded/frictional/no-separation contacts, contact stiffness, convergence and load transfer.
Inputs: contact surfaces, friction, preload, expected separation/sliding.
Decision logic: bonded contacts can over-stiffen; frictional contacts require convergence checks.
""",
        "mesh_convergence.md": """
# Mesh Convergence Expert Pack
Scope: element quality, refinement strategy, local stress, displacement and reaction convergence.
Inputs: geometry, stress gradients, element type, result target.
Decision logic: validate quantities of interest, not just pretty plots; singularities should not drive design decisions.
""",
        "validation.md": """
# FEA Validation Expert Pack
Scope: analytical checks, test correlation, benchmark cases, sanity checks and uncertainty.
Inputs: expected load path, hand calc, test data, acceptance criteria.
Decision logic: simulation without validation is evidence-limited; define acceptance before solving.
""",
    },
    "cfd_thermal": {
        "internal_flow.md": """
# Internal Flow CFD Expert Pack
Scope: pipe/duct/channel flow, pressure drop, flow regime, thermal flow and boundary conditions.
Inputs: fluid, density, viscosity, flow rate/velocity, diameter, roughness, temperature, inlet/outlet conditions.
Decision logic: calculate Reynolds number first; validate pressure drop against correlations; check mass conservation.
""",
        "external_flow.md": """
# External Flow CFD Expert Pack
Scope: aerodynamic/hydrodynamic external flow, domain sizing, far-field boundaries and wake refinement.
Inputs: velocity, fluid, characteristic length, domain, turbulence intensity, target coefficients.
Decision logic: domain size and boundary placement affect results; mesh wake and boundary layer carefully.
""",
        "reynolds_number.md": """
# Reynolds Number Expert Pack
Re = rho*V*D/mu. It classifies flow regime and drives laminar/turbulent model selection.
Typical pipe thresholds: laminar below about 2300, transitional around 2300-4000, turbulent above about 4000.
""",
        "turbulence_models.md": """
# Turbulence Models Expert Pack
Scope: k-epsilon, k-omega SST, laminar and transitional modeling.
Decision logic: use model based on physics, y+, wall treatment, separation, adverse pressure gradient and validation needs.
""",
        "y_plus.md": """
# y+ Expert Pack
Scope: wall resolution for turbulence modeling.
Decision logic: low-Re wall-resolved methods often require y+ near 1; wall functions use higher y+. State target before meshing.
""",
        "pressure_drop.md": """
# Pressure Drop Expert Pack
Scope: pipe/duct pressure loss, friction factor, minor losses and validation.
Equation: Darcy-Weisbach deltaP=f*(L/D)*(rho*V^2/2) plus minor losses.
""",
        "heat_transfer.md": """
# Heat Transfer Expert Pack
Scope: convection, conduction, thermal resistance, heat sinks and thermal validation.
Equation examples: q=h*A*deltaT, conduction q=k*A*deltaT/L, thermal resistance networks.
""",
    },
    "cad_solidworks": {
        "macro_generation.md": """
# SolidWorks Macro Generation Expert Pack
Scope: VBA macro generation, model/document access, selection, export and error handling.
Rules: use explicit object variables; check active document; avoid destructive operations; validate paths; include error handler.
""",
        "macro_validation.md": """
# SolidWorks Macro Validation Expert Pack
Check: option explicit, active document guard, type check, save path validation, error handling, no silent overwrite, clear user instructions.
""",
        "batch_export_workflows.md": """
# Batch Export Workflow Expert Pack
Scope: exporting STEP, DXF, PDF, drawings and flat patterns.
Rules: create backup, decide naming convention, handle assemblies/drawings/parts differently, log success/failure per file.
""",
        "drawing_automation.md": """
# Drawing Automation Expert Pack
Scope: views, dimensions, sheets, title block, revision notes and PDF export.
Rules: never assume drawing standard; request template, units, projection, tolerance style.
""",
        "bom_export.md": """
# BOM Export Expert Pack
Scope: assembly BOM extraction, custom properties, part numbers, quantities, materials, revisions.
Rules: define property mapping and handle virtual components/suppressed parts.
""",
    },
    "innovation_patent": {
        "idea_evaluation.md": """
# Idea Evaluation Expert Pack
Scope: problem-solution fit, novelty, technical feasibility, manufacturability and business value.
Decision logic: separate what is new, useful, manufacturable and commercially valuable.
""",
        "prior_art_search.md": """
# Prior Art Search Expert Pack
Scope: keyword/classification search, competitor scan, functional decomposition and claim risk.
Decision logic: search by function, mechanism, outcome, application and alternative terminology.
""",
        "claim_structure.md": """
# Claim Structure Expert Pack
Scope: independent/dependent claim thinking for engineering inventions.
Warning: not legal advice; patent attorney review required.
""",
        "prototype_strategy.md": """
# Prototype Strategy Expert Pack
Scope: proof of principle, functional prototype, design validation and pilot manufacturing.
Decision logic: prototype the riskiest assumptions first.
""",
    },
}

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def slugify(text: str, fallback: str = "item") -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9\u0600-\u06FF]+", "_", text)
    text = text.strip("_")
    return text or fallback


def safe_read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def safe_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def strip_md(text: str) -> str:
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"\*\*|__|`", "", text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z0-9_\u0600-\u06FF]+", text.lower())
    stop = {"the", "and", "for", "with", "that", "this", "from", "into", "what", "how", "create", "review", "analysis", "please", "عايز", "اعمل", "ايه", "في", "من", "على", "عن"}
    return [w for w in words if len(w) > 2 and w not in stop]


def file_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def write_file(path: Path, data: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8")


def seed_knowledge_library() -> None:
    for folder, files in KNOWLEDGE_SEED.items():
        target = GLOBAL_KNOWLEDGE_DIR / folder
        target.mkdir(parents=True, exist_ok=True)
        for name, text in files.items():
            f = target / name
            if not f.exists() or len(f.read_text(encoding="utf-8", errors="ignore")) < 50:
                f.write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")


def extract_uploaded_text(uploaded) -> str:
    name = uploaded.name.lower()
    data = uploaded.getvalue()
    if name.endswith(".pdf") and PyPDF2 is not None:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(data))
            pages = []
            for p in reader.pages[:80]:
                pages.append(p.extract_text() or "")
            return "\n".join(pages)
        except Exception as e:
            return f"[PDF extraction failed: {e}]"
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return "[Could not decode file as text.]"


def ensure_state() -> None:
    defaults = {
        "messages": [],
        "active_project_id": None,
        "template_to_use": "",
        "show_new_project": False,
        "active_tab": "Chat",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# -----------------------------------------------------------------------------
# Data paths and project system
# -----------------------------------------------------------------------------

def tenant_path(workspace_id: str) -> Path:
    return TENANT_DIR / slugify(workspace_id, "personal_workspace")


def tenant_projects_dir(workspace_id: str) -> Path:
    p = tenant_path(workspace_id) / "projects"
    p.mkdir(parents=True, exist_ok=True)
    return p


def users_file(workspace_id: str) -> Path:
    return tenant_path(workspace_id) / "users.json"


def project_dir(workspace_id: str, project_id: str) -> Path:
    p = tenant_projects_dir(workspace_id) / project_id
    p.mkdir(parents=True, exist_ok=True)
    for sub in ["references", "reports", "artifacts", "uploads"]:
        (p / sub).mkdir(exist_ok=True)
    return p


def list_projects(workspace_id: str) -> List[Dict[str, Any]]:
    projects = []
    for d in tenant_projects_dir(workspace_id).iterdir():
        if d.is_dir() and (d / "project.json").exists():
            data = safe_read_json(d / "project.json", {})
            data["project_id"] = d.name
            projects.append(data)
    projects.sort(key=lambda x: x.get("updated_at", x.get("created_at", "")), reverse=True)
    return projects


def create_project(workspace_id: str, meta: Dict[str, Any]) -> str:
    project_id = slugify(meta.get("project_name", "project")) + "_" + uuid.uuid4().hex[:6]
    p = project_dir(workspace_id, project_id)
    meta.update({"project_id": project_id, "created_at": now_iso(), "updated_at": now_iso(), "workspace_id": workspace_id})
    safe_write_json(p / "project.json", meta)
    memory = {
        "questions": [], "decisions": [], "assumptions": [], "materials": [], "calculations": [],
        "risks": [], "reports": [], "lessons_learned": [], "chat_messages": [], "references": [], "artifacts": []
    }
    safe_write_json(p / "memory.json", memory)
    return project_id


def load_project(workspace_id: str, project_id: Optional[str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if not project_id:
        return {}, {}
    p = project_dir(workspace_id, project_id)
    return safe_read_json(p / "project.json", {}), safe_read_json(p / "memory.json", {})


def save_project(workspace_id: str, project_id: str, meta: Dict[str, Any], memory: Dict[str, Any]) -> None:
    p = project_dir(workspace_id, project_id)
    meta["updated_at"] = now_iso()
    safe_write_json(p / "project.json", meta)
    safe_write_json(p / "memory.json", memory)


def add_memory_item(workspace_id: str, project_id: str, category: str, item: Any) -> None:
    meta, mem = load_project(workspace_id, project_id)
    mem.setdefault(category, []).append(item)
    save_project(workspace_id, project_id, meta, mem)

# -----------------------------------------------------------------------------
# Reference vault and retrieval
# -----------------------------------------------------------------------------

@dataclass
class SourceChunk:
    source_id: str
    title: str
    workspace: str
    path: str
    source_type: str
    confidentiality: str
    revision: str
    tags: List[str]
    text: str
    quality: float = 1.0


def chunk_text(text: str, size: int = 850, overlap: int = 120) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i+size])
        i += max(1, size - overlap)
    return chunks


def source_quality(source_type: str, confidentiality: str) -> float:
    base = {
        "Standards summary": 1.20,
        "Design guide": 1.15,
        "Public datasheet": 1.10,
        "Supplier catalog": 1.00,
        "Open reference": 0.95,
        "Own engineering note": 0.90,
        "Project reference": 0.85,
        "Personal reference": 0.80,
        "Team reference": 0.90,
    }.get(source_type, 0.80)
    if confidentiality in ["Private", "Confidential"]:
        base += 0.05
    return base


def register_reference(workspace_id: str, project_id: str, uploaded, meta: Dict[str, str]) -> Dict[str, Any]:
    p = project_dir(workspace_id, project_id)
    ref_id = uuid.uuid4().hex[:10]
    safe_name = slugify(Path(uploaded.name).stem, "reference") + Path(uploaded.name).suffix.lower()
    raw_path = p / "references" / f"{ref_id}_{safe_name}"
    raw_path.write_bytes(uploaded.getvalue())
    text = extract_uploaded_text(uploaded)
    text_path = p / "references" / f"{ref_id}_extracted.txt"
    text_path.write_text(text, encoding="utf-8", errors="ignore")
    rec = {
        "reference_id": ref_id,
        "filename": uploaded.name,
        "stored_path": str(raw_path.relative_to(ROOT)),
        "text_path": str(text_path.relative_to(ROOT)),
        "title": meta.get("title") or uploaded.name,
        "workspace": meta.get("workspace", "General engineering"),
        "source_type": meta.get("source_type", "Project reference"),
        "confidentiality": meta.get("confidentiality", "Private"),
        "revision": meta.get("revision", "unspecified"),
        "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
        "legal_note": meta.get("legal_note", "User states they have the right to use this reference."),
        "created_at": now_iso(),
    }
    add_memory_item(workspace_id, project_id, "references", rec)
    return rec


def collect_global_sources() -> List[SourceChunk]:
    sources: List[SourceChunk] = []
    for folder in GLOBAL_KNOWLEDGE_DIR.iterdir():
        if not folder.is_dir():
            continue
        workspace = next((k for k, v in WORKSPACES.items() if v["folder"] == folder.name), folder.name)
        for f in folder.glob("*.md"):
            raw = file_text(f)
            for i, c in enumerate(chunk_text(raw)):
                sources.append(SourceChunk(
                    source_id=f"G-{folder.name}-{f.stem}-{i}",
                    title=f.stem.replace("_", " ").title(),
                    workspace=workspace,
                    path=str(f.relative_to(ROOT)),
                    source_type="Global knowledge pack",
                    confidentiality="Public",
                    revision="global",
                    tags=[folder.name, f.stem],
                    text=c,
                    quality=1.0,
                ))
    return sources


def collect_project_sources(workspace_id: str, project_id: Optional[str]) -> List[SourceChunk]:
    if not project_id:
        return []
    _, mem = load_project(workspace_id, project_id)
    sources = []
    for rec in mem.get("references", []):
        text_path = ROOT / rec.get("text_path", "")
        raw = file_text(text_path)
        for i, c in enumerate(chunk_text(raw)):
            sources.append(SourceChunk(
                source_id=f"R-{rec.get('reference_id')}-{i}",
                title=rec.get("title", "Reference"),
                workspace=rec.get("workspace", "General engineering"),
                path=rec.get("stored_path", ""),
                source_type=rec.get("source_type", "Project reference"),
                confidentiality=rec.get("confidentiality", "Private"),
                revision=rec.get("revision", "unspecified"),
                tags=rec.get("tags", []),
                text=c,
                quality=source_quality(rec.get("source_type", "Project reference"), rec.get("confidentiality", "Private")),
            ))
    return sources


def expand_query(query: str, workspace: str, project_meta: Dict[str, Any]) -> str:
    tokens = [query]
    q = query.lower()
    expansions = {
        "Manufacturing / DFM": ["wall thickness draft ribs bosses tooling tolerance assembly process capability sink warpage cycle time quality"],
        "Simulation / FEA": ["loads constraints contacts mesh convergence validation stress displacement failure criteria"],
        "CFD / Thermal": ["reynolds turbulence y plus boundary conditions pressure drop heat transfer convergence mass balance"],
        "CAD / SolidWorks": ["macro vba export step dxf drawing bom active document error handling validation"],
        "Materials Selection": ["strength stiffness toughness density temperature corrosion manufacturability cost availability"],
        "Product R&D / Design": ["load path material safety factor fatigue tolerance validation failure modes"],
        "Innovation / Patent": ["novelty prior art claims prototype manufacturability commercial value"],
    }
    tokens.extend(expansions.get(workspace, []))
    for k in ["part_type", "material", "process", "manufacturing_method", "target_use", "project_type"]:
        v = project_meta.get(k)
        if v:
            tokens.append(str(v))
    if any(w in q for w in ["plastic", "mold", "mould", "abs", "cover", "enclosure"]):
        tokens.append("injection molding thermoplastics abs enclosure cover sink warpage draft ribs bosses")
    if any(w in q for w in ["solidworks", "macro", "step", "dxf", "bom"]):
        tokens.append("solidworks macro vba export step dxf bom drawing")
    if any(w in q for w in ["ansys", "fea", "bracket", "stress", "modal", "buckling"]):
        tokens.append("static structural fea mesh convergence loads constraints validation")
    if any(w in q for w in ["cfd", "flow", "pipe", "reynolds", "thermal", "heat"]):
        tokens.append("cfd thermal reynolds pressure drop turbulence heat transfer")
    return " ".join(tokens)


def retrieve_sources(query: str, workspace: str, project_meta: Dict[str, Any], workspace_id: str, project_id: Optional[str], k: int = 6) -> List[Tuple[float, SourceChunk]]:
    query_expanded = expand_query(query, workspace, project_meta)
    q_tokens = tokenize(query_expanded)
    q_set = set(q_tokens)
    candidates = collect_global_sources() + collect_project_sources(workspace_id, project_id)
    scored: List[Tuple[float, SourceChunk]] = []
    for s in candidates:
        t = tokenize(s.title + " " + s.workspace + " " + " ".join(s.tags) + " " + s.text)
        if not t:
            continue
        counter = {w: t.count(w) for w in set(t)}
        score = sum(counter.get(w, 0) for w in q_set)
        title_bonus = sum(3 for w in q_set if w in tokenize(s.title))
        workspace_bonus = 5 if (workspace == s.workspace or workspace == "General engineering") else 0
        folder = WORKSPACES.get(workspace, {}).get("folder")
        path_bonus = 2 if folder and folder in s.path else 0
        meta_bonus = 1.5 * len(q_set.intersection(set(tokenize(" ".join(s.tags)))))
        final = (score + title_bonus + workspace_bonus + path_bonus + meta_bonus) * s.quality
        if final > 0:
            scored.append((final, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:k]

# -----------------------------------------------------------------------------
# Routing, reasoning, scoring
# -----------------------------------------------------------------------------

def route_workspace(query: str, selected: str) -> str:
    q = query.lower()
    rules = [
        ("CAD / SolidWorks", ["solidworks", "macro", "vba", "step", "dxf", "bom", "drawing"]),
        ("Simulation / FEA", ["fea", "ansys", "stress", "modal", "buckling", "mesh", "constraint", "bracket"]),
        ("CFD / Thermal", ["cfd", "fluent", "flow", "pipe", "reynolds", "pressure drop", "heat", "thermal", "y+"]),
        ("Manufacturing / DFM", ["dfm", "dfa", "manufacturing", "molding", "moulding", "machining", "sheet metal", "tooling", "assembly", "injection"]),
        ("Materials Selection", ["material", "abs", "aluminum", "steel", "plastic", "polymer", "corrosion", "temperature"]),
        ("Innovation / Patent", ["patent", "novel", "invention", "claim", "prior art", "triz"]),
        ("Product R&D / Design", ["design", "shaft", "beam", "bearing", "gear", "spring", "fatigue", "tolerance"]),
    ]
    for ws, keys in rules:
        if any(k in q for k in keys):
            return ws
    return selected


def detect_missing_inputs(workspace: str, query: str, meta: Dict[str, Any]) -> List[str]:
    q = query.lower()
    checks = {
        "Manufacturing / DFM": [
            ("material grade", meta.get("material") or any(x in q for x in ["abs", "pc", "pp", "steel", "aluminum"])),
            ("nominal wall thickness / critical dimensions", bool(re.search(r"\d+(\.\d+)?\s*(mm|cm|inch|in)\b", q))),
            ("CAD/STEP/drawing or geometry description", any(x in q for x in ["cad", "step", "drawing", "rib", "boss", "snap", "cover", "enclosure"])),
            ("annual volume", meta.get("annual_volume") or re.search(r"\d+\s*(pcs|parts|units|year|yr)", q)),
            ("surface finish / cosmetic requirement", any(x in q for x in ["surface", "texture", "cosmetic", "finish"])),
        ],
        "Simulation / FEA": [
            ("study objective", any(x in q for x in ["static", "modal", "buckling", "fatigue", "thermal"])),
            ("material properties", meta.get("material") or any(x in q for x in ["steel", "aluminum", "abs", "pa", "material"])),
            ("loads", any(x in q for x in ["load", "force", "n", "kn", "pressure", "torque"])),
            ("constraints / supports", any(x in q for x in ["fixed", "support", "constraint", "bolted"])),
            ("validation target", any(x in q for x in ["validate", "test", "allowable", "limit"])),
        ],
        "CFD / Thermal": [
            ("fluid and properties", any(x in q for x in ["water", "air", "oil", "density", "viscosity"])),
            ("velocity or flow rate", any(x in q for x in ["m/s", "l/min", "flow", "velocity"])),
            ("characteristic length / diameter", any(x in q for x in ["diameter", "pipe", "mm", "meter", "length"])),
            ("boundary conditions", any(x in q for x in ["inlet", "outlet", "wall", "pressure", "temperature"])),
            ("validation target", any(x in q for x in ["pressure drop", "temperature", "heat", "validate"])),
        ],
        "Materials Selection": [
            ("functional requirements", any(x in q for x in ["strength", "stiff", "impact", "temperature", "chemical", "corrosion"])),
            ("manufacturing process", meta.get("process") or any(x in q for x in ["molding", "machining", "sheet", "weld", "casting"])),
            ("cost/availability target", any(x in q for x in ["cost", "cheap", "available", "supplier"])),
        ],
        "CAD / SolidWorks": [
            ("document type: part/assembly/drawing", any(x in q for x in ["part", "assembly", "drawing"])),
            ("workflow goal", any(x in q for x in ["export", "create", "bom", "dxf", "step", "pdf"])),
            ("file naming / output path", any(x in q for x in ["folder", "path", "name", "save"])),
        ],
    }
    return [name for name, ok in checks.get(workspace, []) if not ok]


def input_maturity(workspace: str, query: str, meta: Dict[str, Any]) -> Tuple[int, str]:
    missing = detect_missing_inputs(workspace, query, meta)
    total = max(5, len(missing) + 2)
    known = max(0, total - len(missing))
    # Bonus for project metadata
    bonus_fields = ["part_type", "material", "process", "annual_volume", "target_use"]
    bonus = sum(1 for f in bonus_fields if meta.get(f))
    score = min(100, int((known / total) * 70 + bonus * 6))
    label = "Preliminary only" if score < 45 else "Developing" if score < 70 else "Review-ready" if score < 85 else "Strong input maturity"
    return score, label


def confidence_level(maturity_score: int, retrieved_count: int, calc_count: int) -> str:
    raw = maturity_score + retrieved_count * 4 + calc_count * 6
    if raw >= 90:
        return "High"
    if raw >= 70:
        return "Medium-high"
    if raw >= 50:
        return "Medium"
    if raw >= 35:
        return "Low-to-medium"
    return "Low"


def release_gate(maturity_score: int, high_risks: int, unknowns: int) -> str:
    if high_risks >= 3 or maturity_score < 35:
        return "Engineering hold — preliminary only"
    if unknowns >= 3 or maturity_score < 60:
        return "Conditional pass — more inputs required before release"
    if high_risks == 0 and unknowns <= 1 and maturity_score >= 75:
        return "Review pass — suitable for next engineering gate"
    return "Conditional pass — verify risks before release"


def risk_matrix(workspace: str, query: str, meta: Dict[str, Any]) -> List[Dict[str, str]]:
    q = query.lower()
    if workspace == "Manufacturing / DFM":
        rows = [
            ("Wall thickness", "High" if not re.search(r"\d+(\.\d+)?\s*mm", q) else "Medium", "No nominal wall thickness was provided."),
            ("Draft / ejection", "Medium", "Injection molded parts require release angle and ejection planning."),
            ("Ribs / bosses", "High" if any(x in q for x in ["cover", "enclosure", "boss", "rib"]) else "Medium", "Covers often require stiffness and mounting features; thick bosses create sink risk."),
            ("Tooling strategy", "Medium", "Gate, parting line and ejector strategy are not defined."),
            ("Tolerance capability", "Unknown", "CTQ dimensions and tolerance limits are missing."),
            ("Assembly / DFA", "Unknown", "Mating parts and assembly method are not defined."),
        ]
    elif workspace == "Simulation / FEA":
        rows = [
            ("Objective", "Medium", "Study type and pass/fail criteria must be explicit."),
            ("Loads", "Medium" if any(x in q for x in ["load", "force", "kn", "n"]) else "High", "Loads are incomplete or need verification."),
            ("Constraints", "High" if not any(x in q for x in ["fixed", "support", "constraint"]) else "Medium", "Incorrect constraints can invalidate FEA."),
            ("Contacts", "Unknown", "Contact/bonding assumptions are not defined."),
            ("Mesh convergence", "High", "No convergence plan provided."),
            ("Validation", "High", "No hand calculation or test correlation target provided."),
        ]
    elif workspace == "CFD / Thermal":
        rows = [
            ("Flow regime", "Medium" if any(x in q for x in ["reynolds", "water", "air", "m/s"]) else "High", "Flow regime drives model selection."),
            ("Boundary conditions", "High" if not any(x in q for x in ["inlet", "outlet", "wall", "temperature"]) else "Medium", "CFD is highly sensitive to boundary conditions."),
            ("Turbulence model", "Medium", "Model should be justified by Re, y+ and separation risk."),
            ("Mesh / y+", "High", "No wall-resolution target or mesh plan provided."),
            ("Convergence", "Medium", "Residual and balance targets are not specified."),
            ("Validation", "High", "No analytical or experimental reference defined."),
        ]
    elif workspace == "CAD / SolidWorks":
        rows = [
            ("Document safety", "High", "Macro must guard against no active document and wrong document type."),
            ("File overwrite", "High", "Output path and overwrite behavior must be controlled."),
            ("Error handling", "Medium", "Macro should include explicit error handling and logging."),
            ("Workflow completeness", "Medium", "Export, drawing/BOM and naming convention must be clarified."),
        ]
    elif workspace == "Materials Selection":
        rows = [
            ("Functional requirements", "High", "Material cannot be selected from material name alone."),
            ("Environment", "Medium", "Temperature, chemicals and UV exposure are not fully defined."),
            ("Manufacturing compatibility", "Medium", "Process compatibility must be checked."),
            ("Availability / cost", "Unknown", "Supplier and cost targets are missing."),
        ]
    else:
        rows = [
            ("Requirements clarity", "Medium", "Function, loads and constraints are partially defined."),
            ("Validation plan", "High", "Verification method is not specified."),
            ("Manufacturing compatibility", "Medium", "Process constraints are not fully defined."),
        ]
    return [{"Area": a, "Risk": r, "Reason": reason} for a, r, reason in rows]


def score_from_risks(rows: List[Dict[str, str]], base: int = 100) -> int:
    penalty = {"High": 14, "Medium": 8, "Low": 3, "Unknown": 10}
    s = base - sum(penalty.get(r.get("Risk", "Medium"), 6) for r in rows)
    return max(0, min(100, s))

# -----------------------------------------------------------------------------
# Engineering calculators
# -----------------------------------------------------------------------------

def calc_beam_center_load(P: float, L: float, E: float, I: float) -> Dict[str, float]:
    return {"M_max_Nm": P * L / 4, "deflection_m": P * L**3 / (48 * E * I)}


def calc_shaft_torsion(T: float, d: float, L: float, G: float) -> Dict[str, float]:
    J = math.pi * d**4 / 32
    tau = 16 * T / (math.pi * d**3)
    theta = T * L / (J * G)
    return {"polar_J_m4": J, "tau_Pa": tau, "twist_rad": theta, "twist_deg": theta * 180 / math.pi}


def calc_bearing_l10(C: float, P: float, rpm: float, p_exp: float = 3.0) -> Dict[str, float]:
    L10_mrev = (C / P) ** p_exp
    L10_h = (1e6 / (60 * rpm)) * L10_mrev
    return {"L10_million_rev": L10_mrev, "L10_hours": L10_h}


def calc_reynolds(rho: float, V: float, D: float, mu: float) -> Dict[str, Any]:
    Re = rho * V * D / mu
    regime = "Laminar" if Re < 2300 else "Transitional" if Re < 4000 else "Turbulent"
    return {"Re": Re, "regime": regime}


def calc_pressure_drop(f: float, L: float, D: float, rho: float, V: float, k_minor: float = 0.0) -> Dict[str, float]:
    dynamic = rho * V**2 / 2
    dp = (f * L / D + k_minor) * dynamic
    return {"dynamic_pressure_Pa": dynamic, "deltaP_Pa": dp}


def calc_heat_transfer(h: float, A: float, dT: float) -> Dict[str, float]:
    return {"q_W": h * A * dT}


def calc_sheet_metal_bend(angle_deg: float, radius: float, thickness: float, k_factor: float) -> Dict[str, float]:
    ba = math.radians(angle_deg) * (radius + k_factor * thickness)
    return {"bend_allowance_mm": ba}


def calc_fastener_preload(proof_load_N: float, preload_fraction: float = 0.75) -> Dict[str, float]:
    return {"recommended_preload_N": proof_load_N * preload_fraction}


def calc_spring_rate(G: float, wire_d: float, mean_D: float, active_coils: float) -> Dict[str, float]:
    k = G * wire_d**4 / (8 * mean_D**3 * active_coils)
    return {"spring_rate_N_per_m": k}


def injection_molding_check(wall_mm: Optional[float], rib_mm: Optional[float], boss_mm: Optional[float]) -> List[Dict[str, str]]:
    out = []
    if wall_mm is None:
        out.append({"Check": "Wall thickness", "Status": "Unknown", "Advice": "Provide nominal wall thickness."})
    else:
        status = "Review" if wall_mm < 1.0 or wall_mm > 4.0 else "Preliminary OK"
        out.append({"Check": "Wall thickness", "Status": status, "Advice": "Keep wall uniform and verify material-specific range."})
    if rib_mm is not None and wall_mm:
        ratio = rib_mm / wall_mm
        out.append({"Check": "Rib thickness ratio", "Status": "High risk" if ratio > 0.7 else "Preliminary OK", "Advice": "Ribs are often kept thinner than wall to reduce sink; validate by material/tooling."})
    if boss_mm is not None and wall_mm:
        ratio = boss_mm / wall_mm
        out.append({"Check": "Boss thickness ratio", "Status": "High risk" if ratio > 1.0 else "Review", "Advice": "Avoid thick bosses; use cored bosses and supporting ribs."})
    return out


def parse_basic_numbers_for_calcs(query: str) -> List[Dict[str, Any]]:
    q = query.lower()
    calcs = []
    # Reynolds: water in 20 mm pipe at 1 m/s
    m_d = re.search(r"(\d+(?:\.\d+)?)\s*mm", q)
    m_v = re.search(r"(\d+(?:\.\d+)?)\s*m/s", q)
    if any(x in q for x in ["reynolds", "pipe", "flow"]) and m_d and m_v:
        D = float(m_d.group(1)) / 1000
        V = float(m_v.group(1))
        rho = 1000.0 if "water" in q else 1.225 if "air" in q else 1000.0
        mu = 0.001 if "water" in q else 1.81e-5 if "air" in q else 0.001
        calcs.append({"name": "Reynolds number", "result": calc_reynolds(rho, V, D, mu)})
    return calcs

# -----------------------------------------------------------------------------
# CAD and simulation artifacts
# -----------------------------------------------------------------------------

def generate_solidworks_macro(workflow: str, project_name: str = "MechAI_Project") -> str:
    workflow_comment = workflow.replace("'", "")[:200]
    return f'''Option Explicit

' MechAI Pro generated SolidWorks VBA macro skeleton
' Project: {project_name}
' Workflow intent: {workflow_comment}
' Safety: Review paths and backup files before running.

Dim swApp As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim swExt As SldWorks.ModelDocExtension
Dim errors As Long
Dim warnings As Long

Sub main()
    On Error GoTo EH
    Set swApp = Application.SldWorks
    Set swModel = swApp.ActiveDoc
    If swModel Is Nothing Then
        MsgBox "No active SolidWorks document. Open a part/assembly/drawing first.", vbCritical
        Exit Sub
    End If
    Set swExt = swModel.Extension

    Dim docTitle As String
    docTitle = swModel.GetTitle

    Dim outFolder As String
    outFolder = Environ$("USERPROFILE") & "\\Desktop\\MechAI_Exports"
    If Dir(outFolder, vbDirectory) = "" Then MkDir outFolder

    ' TODO: customize naming convention and workflow here.
    ' Example STEP export:
    Dim stepPath As String
    stepPath = outFolder & "\\" & docTitle & ".step"
    swExt.SaveAs stepPath, 0, 0, Nothing, errors, warnings

    ' Example drawing/DXF/BOM automation should be added according to document type.
    MsgBox "MechAI macro completed. Check export folder: " & outFolder, vbInformation
    Exit Sub
EH:
    MsgBox "Macro failed: " & Err.Description, vbCritical
End Sub
'''


def validate_macro_text(code: str) -> List[Dict[str, str]]:
    checks = [
        ("Option Explicit", "Option Explicit" in code),
        ("Active document guard", "ActiveDoc" in code and "Is Nothing" in code),
        ("Error handler", "On Error" in code and "EH:" in code),
        ("Export path", "outFolder" in code or "SaveAs" in code),
        ("Overwrite awareness", "backup" in code.lower() or "review paths" in code.lower()),
    ]
    return [{"Check": c, "Status": "Pass" if ok else "Review"} for c, ok in checks]


def generate_apdl(project: str, load_hint: str = "") -> str:
    return f'''! MechAI Pro ANSYS APDL starter
! Project: {project}
/PREP7
! TODO: Define material properties
MP,EX,1,2.1e11
MP,PRXY,1,0.3
! TODO: Import/define geometry and mesh
! TODO: Apply boundary conditions and loads: {load_hint}
/SOLU
ANTYPE,0
SOLVE
/POST1
! TODO: Review displacement, stress, reactions, convergence evidence
FINISH
'''


def generate_fluent_journal(project: str) -> str:
    return f'''; MechAI Pro Fluent journal starter
; Project: {project}
; TODO: Read mesh
; /file/read-mesh mesh.msh
; TODO: Set models based on Reynolds number and physics
; /define/models/viscous k-omega-sst yes
; TODO: Set material, boundary conditions, initialization, convergence monitors
; /solve/initialize/hyb-initialization
; /solve/iterate 500
; TODO: Check mass/energy balance and validation targets
'''


def fea_setup_score(query: str, meta: Dict[str, Any]) -> Tuple[int, List[Dict[str, str]]]:
    rows = risk_matrix("Simulation / FEA", query, meta)
    score = score_from_risks(rows)
    return score, rows


def cfd_setup_score(query: str, meta: Dict[str, Any]) -> Tuple[int, List[Dict[str, str]]]:
    rows = risk_matrix("CFD / Thermal", query, meta)
    score = score_from_risks(rows)
    return score, rows

# -----------------------------------------------------------------------------
# Templates, reports, tests
# -----------------------------------------------------------------------------

TEMPLATES = {
    "DFM Review Template": "Create a DFM review for [part]. Process: [process]. Material: [material]. Annual volume: [volume]. Include score, risk matrix, missing inputs and verification plan.",
    "FEA Setup Review Template": "Create an FEA setup review for [part]. Loads: [loads]. Constraints: [constraints]. Material: [material]. Include mesh, contacts, convergence and validation plan.",
    "CFD Setup Review Template": "Create a CFD setup review for [flow domain]. Fluid: [fluid]. Velocity/flow rate: [value]. Include Reynolds number, turbulence model, mesh/y+, convergence and validation.",
    "Material Selection Matrix": "Create a material selection matrix for [part/function]. Requirements: strength, stiffness, temperature, chemicals, process, cost, availability.",
    "Design Review Checklist": "Create a design review checklist for [product]. Include requirements, loads, materials, manufacturing, tolerances, risks and verification.",
    "FMEA Template": "Create an FMEA for [system/part]. Include function, failure modes, effects, causes, controls, severity, occurrence, detection and actions.",
    "DVP&R Template": "Create a DVP&R plan for [product]. Include requirements, test method, acceptance criteria, sample size, owner and status.",
    "Cost Reduction Template": "Create a cost reduction review for [part/process]. Include material, process, tooling, assembly, inspection, scrap, and ranked cost-down actions.",
    "SolidWorks Macro Request Template": "Generate a SolidWorks VBA macro for [workflow]. Include validation, safety notes, .bas export and run instructions.",
}


def build_report_markdown(workspace_id: str, project_id: str, title: str = "Engineering Report") -> str:
    meta, mem = load_project(workspace_id, project_id)
    lines = [f"# {title}", "", f"Generated: {now_iso()}", f"App: {APP_TITLE} {APP_VERSION}", ""]
    lines += ["## Project Profile"]
    for k, v in meta.items():
        if k not in ["project_id"] and v:
            lines.append(f"- **{k.replace('_',' ').title()}**: {v}")
    for sec in ["assumptions", "risks", "decisions", "materials", "calculations", "lessons_learned", "references"]:
        lines.append(f"\n## {sec.replace('_',' ').title()}")
        items = mem.get(sec, [])
        if not items:
            lines.append("- None recorded yet.")
        else:
            for item in items[-20:]:
                if isinstance(item, dict):
                    lines.append("- " + "; ".join(f"{k}: {v}" for k, v in item.items() if k not in ["text"] and v))
                else:
                    lines.append(f"- {item}")
    lines.append("\n## Conversation Excerpts")
    for m in mem.get("chat_messages", [])[-10:]:
        lines.append(f"### {m.get('role','message').title()} — {m.get('created_at','')}")
        lines.append(str(m.get("content", ""))[:2000])
        lines.append("")
    return "\n".join(lines)


def markdown_to_docx_bytes(md: str) -> Optional[bytes]:
    if Document is None:
        return None
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
        else:
            doc.add_paragraph(strip_md(line))
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def markdown_to_pdf_bytes(md: str) -> Optional[bytes]:
    if canvas is None or A4 is None:
        return None
    bio = io.BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    width, height = A4
    y = height - 40
    c.setFont("Helvetica", 9)
    for raw in md.splitlines():
        line = strip_md(raw)
        for part in textwrap.wrap(line, width=95) or [""]:
            if y < 40:
                c.showPage(); c.setFont("Helvetica", 9); y = height - 40
            c.drawString(40, y, part[:140])
            y -= 13
    c.save()
    return bio.getvalue()


def memory_to_xlsx_bytes(workspace_id: str, project_id: str) -> Optional[bytes]:
    if Workbook is None:
        return None
    meta, mem = load_project(workspace_id, project_id)
    wb = Workbook()
    ws = wb.active
    ws.title = "Project Profile"
    ws.append(["Field", "Value"])
    for k, v in meta.items():
        ws.append([k, str(v)])
    for sec in ["assumptions", "risks", "decisions", "materials", "calculations", "reports", "lessons_learned"]:
        sheet = wb.create_sheet(sec[:31])
        sheet.append(["Index", "Data"])
        for i, item in enumerate(mem.get(sec, []), 1):
            sheet.append([i, json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else str(item)])
    bio = io.BytesIO(); wb.save(bio); return bio.getvalue()


def project_export_zip(workspace_id: str, project_id: str) -> bytes:
    p = project_dir(workspace_id, project_id)
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
        for path in p.rglob("*"):
            if path.is_file():
                z.write(path, path.relative_to(p.parent))
        md = build_report_markdown(workspace_id, project_id, "Project Export Summary")
        z.writestr(f"{project_id}/project_summary.md", md)
    return bio.getvalue()


def run_quality_tests() -> List[Dict[str, Any]]:
    cases = [
        {"name": "DFM injection molded cover", "query": "Create a DFM review for an injection molded plastic cover.", "must": ["Wall thickness", "Draft", "Ribs", "Tooling"]},
        {"name": "FEA bracket", "query": "Create an ANSYS static structural setup plan for a bracket loaded by 2 kN.", "must": ["Loads", "Constraints", "Mesh", "Validation"]},
        {"name": "CFD pipe", "query": "Calculate Reynolds number for water in a 20 mm pipe at 1 m/s.", "must": ["Reynolds", "Flow regime"]},
        {"name": "SolidWorks macro", "query": "Generate a SolidWorks macro skeleton to export STEP and DXF files.", "must": ["Active document", "Export", "Error"]},
    ]
    results = []
    for c in cases:
        ws = route_workspace(c["query"], "General engineering")
        answer = build_engineering_answer(c["query"], ws, {}, "demo", None, for_test=True)
        passed = sum(1 for m in c["must"] if m.lower() in answer.lower())
        results.append({"Case": c["name"], "Workspace": ws, "Passed markers": f"{passed}/{len(c['must'])}", "Status": "Pass" if passed == len(c["must"]) else "Review"})
    return results

# -----------------------------------------------------------------------------
# Answer builder
# -----------------------------------------------------------------------------

def format_source_list(results: List[Tuple[float, SourceChunk]]) -> str:
    lines = []
    for i, (score, s) in enumerate(results, 1):
        lines.append(f"- [K{i}] {s.title} — `{s.path}` — source type: {s.source_type} — confidence weight: {s.quality:.2f}")
    return "\n".join(lines) if lines else "- No internal source matched strongly. Use the global reasoning protocol and ask for more references."


def verification_plan(workspace: str) -> List[str]:
    if workspace == "Manufacturing / DFM":
        return [
            "Collect CAD/STEP or drawings with wall thickness, ribs, bosses, datum and CTQ dimensions.",
            "Define material grade, shrinkage data, production volume, surface class and assembly method.",
            "Run process-specific DFM review for tooling, sink/warpage, draft, parting line, ejection and tolerance capability.",
            "Create first-article inspection plan and process capability targets for CTQ dimensions.",
        ]
    if workspace == "Simulation / FEA":
        return [
            "Freeze the simulation objective and pass/fail criterion before solving.",
            "Confirm material properties, load cases, constraints, contacts and expected load path.",
            "Run mesh convergence on quantity of interest and compare with a hand calculation.",
            "Document limitations, singularities, reaction balance and validation evidence.",
        ]
    if workspace == "CFD / Thermal":
        return [
            "Define fluid, geometry domain, boundary conditions, flow rate/velocity and temperature assumptions.",
            "Calculate Reynolds number and select turbulence/wall treatment strategy.",
            "Set mesh quality, y+ target, convergence residuals, mass/energy balance checks.",
            "Validate pressure drop/temperature/flow with analytical correlation or test data.",
        ]
    if workspace == "CAD / SolidWorks":
        return [
            "Define document types, naming convention, output folder and overwrite policy.",
            "Validate macro against active document, error handling and save path safety.",
            "Run on copied files first and log success/failure per document.",
        ]
    return [
        "Define requirements, assumptions and pass/fail criteria.",
        "Check internal sources and run relevant calculators.",
        "Validate recommendation using hand calculation, prototype or test evidence.",
    ]


def build_engineering_answer(query: str, workspace: str, project_meta: Dict[str, Any], workspace_id: str, project_id: Optional[str], for_test: bool = False) -> str:
    routed = route_workspace(query, workspace)
    sources = retrieve_sources(query, routed, project_meta, workspace_id, project_id, k=6)
    calcs = parse_basic_numbers_for_calcs(query)
    missing = detect_missing_inputs(routed, query, project_meta)
    maturity, maturity_label = input_maturity(routed, query, project_meta)
    risks = risk_matrix(routed, query, project_meta)
    score = score_from_risks(risks)
    high_risks = sum(1 for r in risks if r["Risk"] == "High")
    unknowns = sum(1 for r in risks if r["Risk"] == "Unknown")
    conf = confidence_level(maturity, len(sources), len(calcs))
    gate = release_gate(maturity, high_risks, unknowns)
    agent = WORKSPACES.get(routed, WORKSPACES["General engineering"])["agent"]
    project_frame = []
    for key in ["project_name", "project_type", "part_type", "material", "process", "manufacturing_method", "annual_volume", "target_use"]:
        if project_meta.get(key):
            project_frame.append(f"- {key.replace('_',' ').title()}: {project_meta.get(key)}")
    if not project_frame:
        project_frame = ["- No active project metadata. Create a project to improve context and confidence."]

    lines = []
    lines.append(f"## Mechanical Engineering OS Review — {routed}")
    lines.append("")
    lines.append(f"**Agent:** {agent}")
    lines.append("**Mode:** Internal Knowledge Only")
    lines.append(f"**Build:** {APP_VERSION}")
    lines.append(f"**Release gate:** {gate}")
    lines.append(f"**Input maturity:** {maturity}/100 — {maturity_label}")
    lines.append(f"**Engineering confidence:** {conf}")
    lines.append(f"**Primary score:** {score}/100")
    lines.append("")
    lines.append("### Project frame")
    lines.extend(project_frame)
    lines.append("")
    lines.append("### Engineering interpretation")
    if routed == "Manufacturing / DFM":
        lines.append("The request is treated as a manufacturing feasibility and DFM/DFA review. The current conclusion is preliminary until material, geometry, wall thickness and production volume are defined. For an injection-molded cover, the dominant risks are wall uniformity, draft/ejection, ribs/bosses, sink/warpage, tooling strategy and tolerance capability.")
    elif routed == "Simulation / FEA":
        lines.append("The request is treated as an FEA setup review. The result quality depends mainly on objective definition, loads, constraints, contacts, mesh convergence and validation evidence. The review should not be released from stress plots alone.")
    elif routed == "CFD / Thermal":
        lines.append("The request is treated as a CFD/thermal setup review. Flow regime, boundary conditions, mesh/y+, convergence and mass/energy balance determine result credibility.")
    elif routed == "CAD / SolidWorks":
        lines.append("The request is treated as a CAD automation workflow. Safety, path validation, document-type checking, error handling and non-destructive testing are mandatory before running macros on production files.")
    elif routed == "Materials Selection":
        lines.append("The request is treated as material screening. Material choice must start from function and constraints, not from a preferred material name. Manufacturing compatibility and environment must be checked before recommendation.")
    else:
        lines.append("The request is treated through the global mechanical engineering protocol: define function, loads, constraints, material/process, failure modes, validation method and release gate.")
    lines.append("")
    lines.append("### Risk matrix")
    lines.append("| Area | Risk | Reason |")
    lines.append("|---|---:|---|")
    for r in risks:
        lines.append(f"| {r['Area']} | {r['Risk']} | {r['Reason']} |")
    lines.append("")
    lines.append("### Missing data required before confident release")
    if missing:
        for m in missing:
            lines.append(f"- {m}")
    else:
        lines.append("- No major missing inputs detected from the current prompt, but verify all project requirements.")
    lines.append("")
    if calcs:
        lines.append("### Deterministic calculator results")
        for c in calcs:
            lines.append(f"**{c['name']}**")
            for k, v in c["result"].items():
                if isinstance(v, float):
                    lines.append(f"- {k}: {v:.5g}")
                else:
                    lines.append(f"- {k}: {v}")
        lines.append("")
    lines.append("### Ranked engineering actions")
    actions = []
    for r in risks:
        if r["Risk"] in ["High", "Unknown"]:
            actions.append(f"Resolve **{r['Area']}**: {r['Reason']}")
    actions += verification_plan(routed)[:3]
    for i, a in enumerate(actions[:8], 1):
        lines.append(f"{i}. {a}")
    lines.append("")
    lines.append("### Verification plan")
    for i, step in enumerate(verification_plan(routed), 1):
        lines.append(f"{i}. {step}")
    lines.append("")
    lines.append("### Internal retrieval evidence")
    lines.append(format_source_list(sources))
    lines.append("")
    lines.append("### Engineering warning")
    lines.append("This is an engineering decision-support review. Final design release still requires responsible engineer approval, correct inputs, validated calculations, and applicable standards/compliance checks.")
    answer = "\n".join(lines)
    if not for_test and project_id:
        add_memory_item(workspace_id, project_id, "questions", {"question": query, "workspace": routed, "created_at": now_iso()})
        add_memory_item(workspace_id, project_id, "risks", {"workspace": routed, "score": score, "release_gate": gate, "risk_matrix": risks, "created_at": now_iso()})
        for c in calcs:
            add_memory_item(workspace_id, project_id, "calculations", {"name": c["name"], "result": c["result"], "created_at": now_iso()})
        add_memory_item(workspace_id, project_id, "chat_messages", {"role": "user", "content": query, "created_at": now_iso()})
        add_memory_item(workspace_id, project_id, "chat_messages", {"role": "assistant", "content": answer, "created_at": now_iso()})
    return answer

# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------

def inject_css() -> None:
    st.markdown("""
<style>
:root { --bg:#0f0f10; --panel:#171719; --muted:#9ca3af; --line:#2a2a2d; --text:#f4f4f5; }
html, body, [data-testid="stAppViewContainer"] { background:#0f0f10 !important; color:#f4f4f5; }
[data-testid="stSidebar"] { background:#171719 !important; min-width:290px !important; width:290px !important; }
[data-testid="stSidebar"] * { color:#f4f4f5; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] { display:none !important; }
.block-container { max-width:980px; padding-top:1.2rem; padding-bottom:8rem; }
.stChatMessage { background:transparent !important; }
[data-testid="stChatInput"] { background:#0f0f10 !important; }
textarea, input, select { background:#1f1f22 !important; color:#f4f4f5 !important; border-color:#333 !important; }
button { border-radius:10px !important; }
.mechai-badge { display:inline-block; padding:5px 10px; border:1px solid #2f2f33; border-radius:999px; color:#cbd5e1; background:#161619; font-size:12px; margin-right:6px; margin-bottom:6px; }
.mechai-card { border:1px solid #2a2a2d; background:#151517; border-radius:16px; padding:16px; margin:10px 0; }
.small-muted { color:#9ca3af; font-size:12px; }
hr { border-color:#2a2a2d !important; }
</style>
""", unsafe_allow_html=True)


def sidebar_identity() -> Tuple[str, str, str]:
    st.sidebar.markdown("## MechAI Pro")
    st.sidebar.caption("Universal Mechanical Engineering OS")
    workspace_id = st.sidebar.text_input("Workspace", value=st.session_state.get("workspace_id", "personal_workspace"), help="Personal, team, or company workspace ID.")
    user_name = st.sidebar.text_input("User", value=st.session_state.get("user_name", "Engineer"))
    role = st.sidebar.selectbox("Role", ROLES, index=ROLES.index(st.session_state.get("role", "Owner")) if st.session_state.get("role", "Owner") in ROLES else 0)
    st.session_state["workspace_id"] = workspace_id
    st.session_state["user_name"] = user_name
    st.session_state["role"] = role
    # Local account foundation record
    uf = users_file(workspace_id)
    users = safe_read_json(uf, {})
    uid = slugify(user_name, "engineer")
    users[uid] = {"name": user_name, "role": role, "last_seen": now_iso()}
    safe_write_json(uf, users)
    return workspace_id, user_name, role


def sidebar_project_system(workspace_id: str, role: str) -> Optional[str]:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Projects")
    if st.sidebar.button("+ New engineering project", use_container_width=True):
        st.session_state.show_new_project = True
    projects = list_projects(workspace_id)
    labels = [f"{p.get('project_name','Project')} · {p.get('project_type','')[:18]}" for p in projects]
    if projects:
        current_id = st.session_state.get("active_project_id")
        idx = next((i for i, p in enumerate(projects) if p.get("project_id") == current_id), 0)
        chosen = st.sidebar.selectbox("Active project", labels, index=idx, label_visibility="collapsed")
        st.session_state.active_project_id = projects[labels.index(chosen)]["project_id"]
    else:
        st.sidebar.info("No projects yet. Create one to unlock project memory.")
    return st.session_state.get("active_project_id")


def new_project_form(workspace_id: str) -> None:
    if not st.session_state.get("show_new_project"):
        return
    with st.expander("Create Universal Engineering Project", expanded=True):
        with st.form("new_project_form"):
            c1, c2 = st.columns(2)
            with c1:
                project_name = st.text_input("Project name", value="Injection Molded Cover")
                project_type = st.selectbox("Project type", PROJECT_TYPES)
                part_type = st.text_input("Part type", value="Enclosure")
                material = st.text_input("Material", value="ABS")
            with c2:
                process = st.text_input("Process", value="Injection molding")
                manufacturing_method = st.text_input("Manufacturing method", value="Injection molding")
                annual_volume = st.text_input("Annual volume", value="50,000")
                target_use = st.text_input("Target use", value="Consumer product")
            notes = st.text_area("Initial context / requirements", value="Preliminary R&D/DFM project.")
            if st.form_submit_button("Create project", use_container_width=True):
                pid = create_project(workspace_id, {
                    "project_name": project_name, "project_type": project_type, "part_type": part_type,
                    "material": material, "process": process, "manufacturing_method": manufacturing_method,
                    "annual_volume": annual_volume, "target_use": target_use, "initial_notes": notes,
                })
                st.session_state.active_project_id = pid
                st.session_state.show_new_project = False
                st.rerun()


def project_dashboard(workspace_id: str, project_id: Optional[str]) -> None:
    meta, mem = load_project(workspace_id, project_id)
    if not project_id or not meta:
        st.markdown("### Good to see you.")
        st.caption("Create a project to activate project memory, reference vault, reports, CAD/simulation artifacts, and engineering history.")
        return
    st.markdown(f"### {html.escape(meta.get('project_name','Project'))}")
    badges = [
        f"Type: {meta.get('project_type','-')}", f"Part: {meta.get('part_type','-')}", f"Material: {meta.get('material','-')}",
        f"Process: {meta.get('process','-')}", f"Volume: {meta.get('annual_volume','-')}", f"Use: {meta.get('target_use','-')}",
    ]
    st.markdown("".join(f"<span class='mechai-badge'>{html.escape(b)}</span>" for b in badges), unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Questions", len(mem.get("questions", [])))
    c2.metric("Risks", len(mem.get("risks", [])))
    c3.metric("References", len(mem.get("references", [])))
    c4.metric("Reports", len(mem.get("reports", [])))
    with st.expander("Project memory snapshot", expanded=False):
        st.json({k: mem.get(k, [])[-3:] for k in ["assumptions", "risks", "decisions", "materials", "calculations", "lessons_learned"]})


def reference_vault_ui(workspace_id: str, project_id: Optional[str], role: str) -> None:
    st.subheader("Reference Vault")
    if not project_id:
        st.info("Create/select a project first.")
        return
    meta, mem = load_project(workspace_id, project_id)
    st.caption("Upload only files you have the right to use. Do not upload confidential data to a public deployment.")
    can_edit = role in ["Owner", "Admin", "Engineer"]
    if can_edit:
        with st.form("reference_upload_form"):
            uploaded = st.file_uploader("Upload reference", type=["pdf", "txt", "md", "csv"])
            c1, c2 = st.columns(2)
            with c1:
                title = st.text_input("Title")
                ws = st.selectbox("Workspace", list(WORKSPACES.keys()), index=list(WORKSPACES.keys()).index(meta.get("workspace", "General engineering")) if meta.get("workspace") in WORKSPACES else 0)
                source_type = st.selectbox("Source type", SOURCE_TYPES)
            with c2:
                confidentiality = st.selectbox("Confidentiality", CONFIDENTIALITY, index=2)
                revision = st.text_input("Revision", value="Rev A")
                tags = st.text_input("Tags", value="")
            legal = st.text_area("Legal / usage note", value="I have the right to use this file for this project.")
            if st.form_submit_button("Add to Reference Vault", use_container_width=True) and uploaded:
                rec = register_reference(workspace_id, project_id, uploaded, {
                    "title": title or uploaded.name, "workspace": ws, "source_type": source_type,
                    "confidentiality": confidentiality, "revision": revision, "tags": tags, "legal_note": legal,
                })
                st.success(f"Reference added: {rec['title']}")
                st.rerun()
    else:
        st.warning("Viewer role cannot upload references.")
    refs = mem.get("references", [])
    if refs:
        st.markdown("#### Project references")
        rows = [{"Title": r.get("title"), "Workspace": r.get("workspace"), "Type": r.get("source_type"), "Confidentiality": r.get("confidentiality"), "Revision": r.get("revision"), "Tags": ", ".join(r.get("tags", []))} for r in refs]
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No references uploaded yet.")


def templates_ui() -> None:
    st.subheader("Engineering Templates Library")
    st.caption("Use these templates to avoid starting from a blank prompt.")
    cols = st.columns(2)
    for i, (name, text) in enumerate(TEMPLATES.items()):
        with cols[i % 2]:
            with st.expander(name):
                st.code(text, language="text")
                if st.button(f"Use: {name}", key=f"tpl_{name}"):
                    st.session_state.template_to_use = text
                    st.success("Template copied into the prompt helper below.")
    if st.session_state.get("template_to_use"):
        st.text_area("Selected template", value=st.session_state.template_to_use, height=110)


def report_studio_ui(workspace_id: str, project_id: Optional[str]) -> None:
    st.subheader("Engineering Report Studio")
    if not project_id:
        st.info("Create/select a project first.")
        return
    report_type = st.selectbox("Report type", ["DFM Report", "FEA Setup Review", "CFD Setup Review", "Material Selection Report", "Design Review Report", "FMEA", "DVP&R", "Cost-down Report", "Project Summary"])
    md = build_report_markdown(workspace_id, project_id, report_type)
    st.download_button("Download Markdown", md.encode("utf-8"), file_name=f"{slugify(report_type)}.md", mime="text/markdown")
    docx = markdown_to_docx_bytes(md)
    if docx:
        st.download_button("Download Word DOCX", docx, file_name=f"{slugify(report_type)}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    pdf = markdown_to_pdf_bytes(md)
    if pdf:
        st.download_button("Download PDF", pdf, file_name=f"{slugify(report_type)}.pdf", mime="application/pdf")
    xlsx = memory_to_xlsx_bytes(workspace_id, project_id)
    if xlsx:
        st.download_button("Download Excel XLSX", xlsx, file_name=f"{slugify(report_type)}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("Export full project package ZIP", project_export_zip(workspace_id, project_id), file_name=f"{project_id}_package.zip", mime="application/zip")


def calculators_ui(workspace_id: str, project_id: Optional[str]) -> None:
    st.subheader("Engineering Calculators Pro")
    calc = st.selectbox("Calculator", ["Beam bending", "Shaft torsion", "Bearing L10 life", "Reynolds number", "Pressure drop", "Heat transfer", "Tolerance stack-up", "Sheet metal bend allowance", "Injection molding checks", "Fastener preload", "Spring design", "Material screening"])
    result = None
    if calc == "Beam bending":
        c1, c2, c3, c4 = st.columns(4)
        P = c1.number_input("P load [N]", value=100.0)
        L = c2.number_input("L span [m]", value=1.0)
        E = c3.number_input("E [Pa]", value=2.1e11, format="%.4e")
        I = c4.number_input("I [m^4]", value=1e-6, format="%.4e")
        if st.button("Calculate beam"):
            result = calc_beam_center_load(P, L, E, I)
    elif calc == "Shaft torsion":
        c1, c2, c3, c4 = st.columns(4)
        T = c1.number_input("Torque [Nm]", value=50.0)
        d = c2.number_input("Diameter [m]", value=0.02, format="%.4f")
        L = c3.number_input("Length [m]", value=0.5)
        G = c4.number_input("G [Pa]", value=79e9, format="%.4e")
        if st.button("Calculate shaft"):
            result = calc_shaft_torsion(T, d, L, G)
    elif calc == "Bearing L10 life":
        c1, c2, c3, c4 = st.columns(4)
        C = c1.number_input("C rating [N]", value=10000.0)
        P = c2.number_input("Equivalent load P [N]", value=1000.0)
        rpm = c3.number_input("Speed [rpm]", value=1000.0)
        pexp = c4.selectbox("Bearing type exponent", [3.0, 10/3], format_func=lambda x: "Ball p=3" if x == 3.0 else "Roller p=10/3")
        if st.button("Calculate L10"):
            result = calc_bearing_l10(C, P, rpm, pexp)
    elif calc == "Reynolds number":
        c1, c2, c3, c4 = st.columns(4)
        rho = c1.number_input("Density rho [kg/m³]", value=1000.0)
        V = c2.number_input("Velocity V [m/s]", value=1.0)
        D = c3.number_input("Diameter/length D [m]", value=0.02, format="%.4f")
        mu = c4.number_input("Dynamic viscosity mu [Pa.s]", value=0.001, format="%.6f")
        if st.button("Calculate Reynolds"):
            result = calc_reynolds(rho, V, D, mu)
    elif calc == "Pressure drop":
        c1, c2, c3 = st.columns(3)
        f = c1.number_input("Friction factor f", value=0.02, format="%.4f")
        L = c2.number_input("Length L [m]", value=10.0)
        D = c3.number_input("Diameter D [m]", value=0.02, format="%.4f")
        c4, c5, c6 = st.columns(3)
        rho = c4.number_input("Density rho [kg/m³]", value=1000.0)
        V = c5.number_input("Velocity V [m/s]", value=1.0)
        k = c6.number_input("Minor loss K", value=0.0)
        if st.button("Calculate pressure drop"):
            result = calc_pressure_drop(f, L, D, rho, V, k)
    elif calc == "Heat transfer":
        c1, c2, c3 = st.columns(3)
        h = c1.number_input("h [W/m².K]", value=50.0)
        A = c2.number_input("Area [m²]", value=0.1)
        dT = c3.number_input("Delta T [K]", value=20.0)
        if st.button("Calculate heat transfer"):
            result = calc_heat_transfer(h, A, dT)
    elif calc == "Tolerance stack-up":
        st.caption("Worst-case stack-up: sum of absolute tolerances.")
        vals = st.text_input("Enter tolerances separated by comma [mm]", value="0.1,0.05,0.2")
        if st.button("Calculate stack-up"):
            nums = [abs(float(x.strip())) for x in vals.split(",") if x.strip()]
            result = {"worst_case_stack_mm": sum(nums), "rss_stack_mm": math.sqrt(sum(x*x for x in nums))}
    elif calc == "Sheet metal bend allowance":
        c1, c2, c3, c4 = st.columns(4)
        angle = c1.number_input("Bend angle [deg]", value=90.0)
        radius = c2.number_input("Inside radius [mm]", value=1.0)
        th = c3.number_input("Thickness [mm]", value=1.0)
        kf = c4.number_input("K-factor", value=0.33)
        if st.button("Calculate bend allowance"):
            result = calc_sheet_metal_bend(angle, radius, th, kf)
    elif calc == "Injection molding checks":
        c1, c2, c3 = st.columns(3)
        wall = c1.number_input("Wall [mm]", value=2.5)
        rib = c2.number_input("Rib thickness [mm]", value=1.2)
        boss = c3.number_input("Boss wall [mm]", value=2.5)
        if st.button("Run molding checks"):
            result = injection_molding_check(wall, rib, boss)
    elif calc == "Fastener preload":
        c1, c2 = st.columns(2)
        proof = c1.number_input("Proof load [N]", value=10000.0)
        frac = c2.number_input("Preload fraction", value=0.75)
        if st.button("Calculate preload"):
            result = calc_fastener_preload(proof, frac)
    elif calc == "Spring design":
        c1, c2, c3, c4 = st.columns(4)
        G = c1.number_input("G [Pa]", value=79e9, format="%.4e")
        d = c2.number_input("Wire d [m]", value=0.002, format="%.4f")
        D = c3.number_input("Mean coil D [m]", value=0.02, format="%.4f")
        n = c4.number_input("Active coils", value=8.0)
        if st.button("Calculate spring rate"):
            result = calc_spring_rate(G, d, D, n)
    elif calc == "Material screening":
        requirements = st.multiselect("Requirements", ["High stiffness", "High impact", "Chemical resistance", "Low cost", "High temperature", "Low weight", "Corrosion resistance"], default=["High impact", "Low cost"])
        candidates = ["ABS", "PC", "PP", "PA66", "Aluminum 6061", "Mild steel", "Stainless steel 304"]
        if st.button("Screen materials"):
            # Simple transparent heuristic
            scores = []
            for m in candidates:
                score = 50
                if "Low cost" in requirements and m in ["ABS", "PP", "Mild steel"]: score += 15
                if "High impact" in requirements and m in ["PC", "ABS"]: score += 15
                if "High stiffness" in requirements and m in ["Aluminum 6061", "Mild steel", "Stainless steel 304"]: score += 15
                if "Chemical resistance" in requirements and m in ["PP", "Stainless steel 304"]: score += 15
                if "High temperature" in requirements and m in ["PC", "Aluminum 6061", "Mild steel", "Stainless steel 304"]: score += 10
                if "Low weight" in requirements and m in ["ABS", "PP", "PC", "Aluminum 6061"]: score += 10
                if "Corrosion resistance" in requirements and m in ["PP", "Stainless steel 304", "Aluminum 6061"]: score += 10
                scores.append({"Material": m, "Suitability score": min(score, 100)})
            result = sorted(scores, key=lambda x: x["Suitability score"], reverse=True)
    if result is not None:
        st.markdown("#### Result")
        st.json(result)
        if project_id:
            add_memory_item(workspace_id, project_id, "calculations", {"calculator": calc, "result": result, "created_at": now_iso()})


def cad_studio_ui(workspace_id: str, project_id: Optional[str]) -> None:
    st.subheader("CAD / SolidWorks Automation Studio")
    workflow = st.text_area("Workflow request", value="Export the active SolidWorks document as STEP and prepare for DXF export when applicable.")
    if st.button("Generate VBA macro + validation", use_container_width=True):
        meta, _ = load_project(workspace_id, project_id)
        code = generate_solidworks_macro(workflow, meta.get("project_name", "MechAI_Project") if meta else "MechAI_Project")
        validation = validate_macro_text(code)
        st.code(code, language="vb")
        st.dataframe(validation, use_container_width=True, hide_index=True)
        st.download_button("Download .bas macro", code.encode("utf-8"), file_name="mechai_solidworks_macro.bas", mime="text/plain")
        st.download_button("Download validation notes", json.dumps(validation, indent=2).encode("utf-8"), file_name="macro_validation.json", mime="application/json")
        if project_id:
            add_memory_item(workspace_id, project_id, "artifacts", {"type": "SolidWorks macro", "workflow": workflow, "created_at": now_iso()})


def simulation_studio_ui(workspace_id: str, project_id: Optional[str]) -> None:
    st.subheader("FEA / CFD Simulation Studio")
    mode = st.selectbox("Simulation tool", ["FEA setup scoring", "ANSYS APDL starter", "CFD setup scoring", "Fluent journal starter", "SolidWorks Simulation setup notes", "Validation checklist"])
    prompt = st.text_area("Simulation context", value="Bracket loaded by 2 kN. Material and constraints need to be defined.")
    meta, _ = load_project(workspace_id, project_id)
    if st.button("Generate simulation output", use_container_width=True):
        if "FEA" in mode:
            score, rows = fea_setup_score(prompt, meta)
            st.metric("FEA setup quality", f"{score}/100")
            st.dataframe(rows, use_container_width=True, hide_index=True)
        if "CFD" in mode:
            score, rows = cfd_setup_score(prompt, meta)
            st.metric("CFD setup quality", f"{score}/100")
            st.dataframe(rows, use_container_width=True, hide_index=True)
        if "APDL" in mode:
            code = generate_apdl(meta.get("project_name", "MechAI_Project") if meta else "MechAI_Project", prompt)
            st.code(code, language="text")
            st.download_button("Download ANSYS .mac", code.encode("utf-8"), file_name="mechai_ansys_static_starter.mac", mime="text/plain")
        if "Fluent" in mode:
            code = generate_fluent_journal(meta.get("project_name", "MechAI_Project") if meta else "MechAI_Project")
            st.code(code, language="text")
            st.download_button("Download Fluent .jou", code.encode("utf-8"), file_name="mechai_fluent_starter.jou", mime="text/plain")
        if "SolidWorks" in mode:
            notes = """SolidWorks Simulation setup notes:
1. Define study type and objective.
2. Assign verified material properties.
3. Apply fixtures that represent the real support condition.
4. Apply loads with correct direction, distribution and units.
5. Define contacts carefully.
6. Mesh with convergence on quantity of interest.
7. Compare reactions and hand calculations before release.
"""
            st.text(notes)
            st.download_button("Download setup notes", notes.encode("utf-8"), file_name="solidworks_simulation_setup_notes.txt", mime="text/plain")
        if "Validation" in mode:
            plan = verification_plan("Simulation / FEA") + verification_plan("CFD / Thermal")
            st.markdown("\n".join(f"- {x}" for x in plan))


def quality_tests_ui() -> None:
    st.subheader("Evaluation & Quality Testing System")
    st.caption("Regression-style checks to detect whether future versions lose important engineering behavior.")
    if st.button("Run quality tests", use_container_width=True):
        results = run_quality_tests()
        st.dataframe(results, use_container_width=True, hide_index=True)
        passed = sum(1 for r in results if r["Status"] == "Pass")
        st.metric("Quality pass rate", f"{passed}/{len(results)}")


def chat_ui(workspace_id: str, project_id: Optional[str]) -> None:
    workspace = st.selectbox("Workspace", list(WORKSPACES.keys()), index=0)
    if project_id:
        project_dashboard(workspace_id, project_id)
    else:
        project_dashboard(workspace_id, None)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("Ask MechAI about design, DFM, materials, CAD, FEA, CFD, reports...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        meta, _ = load_project(workspace_id, project_id)
        routed = route_workspace(prompt, workspace)
        answer = build_engineering_answer(prompt, routed, meta, workspace_id, project_id)
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})


def main() -> None:
    st.set_page_config(page_title="MechAI Pro", page_icon="⚙️", layout="wide", initial_sidebar_state="expanded")
    inject_css()
    seed_knowledge_library()
    ensure_state()
    workspace_id, user_name, role = sidebar_identity()
    project_id = sidebar_project_system(workspace_id, role)
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Studio", ["Chat", "Project", "Reference Vault", "Templates", "Reports", "Calculators", "CAD / SolidWorks", "Simulation", "Quality Tests", "Admin"], label_visibility="collapsed")
    st.sidebar.markdown("---")
    st.sidebar.caption("Internal Knowledge Only · No OpenAI/Gemini core dependency")
    st.sidebar.caption(f"Build: {APP_VERSION}")
    new_project_form(workspace_id)
    if page == "Chat":
        chat_ui(workspace_id, project_id)
    elif page == "Project":
        project_dashboard(workspace_id, project_id)
        if project_id:
            meta, mem = load_project(workspace_id, project_id)
            with st.expander("Edit project metadata"):
                with st.form("edit_project"):
                    for key in ["project_name", "project_type", "part_type", "material", "process", "manufacturing_method", "annual_volume", "target_use"]:
                        meta[key] = st.text_input(key.replace("_", " ").title(), value=str(meta.get(key, "")))
                    if st.form_submit_button("Save metadata"):
                        save_project(workspace_id, project_id, meta, mem); st.success("Saved.")
            lesson = st.text_area("Add lesson learned")
            if st.button("Save lesson") and lesson:
                add_memory_item(workspace_id, project_id, "lessons_learned", {"text": lesson, "created_at": now_iso(), "by": st.session_state.get("user_name")})
                st.success("Lesson saved.")
    elif page == "Reference Vault":
        reference_vault_ui(workspace_id, project_id, role)
    elif page == "Templates":
        templates_ui()
    elif page == "Reports":
        report_studio_ui(workspace_id, project_id)
    elif page == "Calculators":
        calculators_ui(workspace_id, project_id)
    elif page == "CAD / SolidWorks":
        cad_studio_ui(workspace_id, project_id)
    elif page == "Simulation":
        simulation_studio_ui(workspace_id, project_id)
    elif page == "Quality Tests":
        quality_tests_ui()
    elif page == "Admin":
        st.subheader("Admin / Multi-tenant Foundation")
        st.info("This Streamlit build provides local workspace/user foundations. For production multi-tenant use, move identity, files and projects to a real database/storage layer.")
        st.write("Workspace:", workspace_id)
        st.write("User:", user_name)
        st.write("Role:", role)
        projects = list_projects(workspace_id)
        st.dataframe(projects, use_container_width=True, hide_index=True)
        if project_id:
            st.download_button("Download active project package", project_export_zip(workspace_id, project_id), file_name=f"{project_id}_package.zip", mime="application/zip")

if __name__ == "__main__":
    main()
