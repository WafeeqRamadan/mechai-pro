# -*- coding: utf-8 -*-
"""
MechAI Pro v22 — Manufacturing / DFM Expert Brain
- Internal knowledge packs are the primary reference brain.
- Adds an expert Manufacturing/DFM reasoning layer: process capability, tooling, tolerance, cost, quality, and validation logic.
- No visible external AI provider UI.
- Fixed sidebar, minimal ChatGPT-like interface.
Run: streamlit run app.py
"""
from __future__ import annotations

import html
import math
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import streamlit as st

APP_DIR = Path(__file__).parent
KNOWLEDGE_DIR = APP_DIR / "knowledge_packs"
BUILD_ID = "V22_DFM_EXPERT_BRAIN_2026_06_13"

# -----------------------------------------------------------------------------
# Mechanical Scientist Brain v22: ontology + protocols
# -----------------------------------------------------------------------------
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

AGENTS = {
    "chief": "🧠 Chief Engineer",
    "mechanical": "🔧 Mechanical Design Scientist",
    "solidworks": "🧩 CAD Automation Specialist",
    "fea": "📊 FEA Simulation Scientist",
    "cfd": "🌊 CFD / Thermal Scientist",
    "manufacturing": "🏭 Manufacturing DFM/DFA Scientist",
    "materials": "🧪 Materials Selection Scientist",
    "patent": "💡 Innovation / Patent Reasoning",
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

INTENT_KEYWORDS = {
    "mechanical": ["design", "shaft", "bearing", "spring", "gear", "stress", "fatigue", "load", "safety factor", "tolerance", "gd&t", "mechanism", "bracket", "housing", "beam", "deflection"],
    "solidworks": ["solidworks", "macro", "vba", "api", "part", "assembly", "drawing", "bom", "step", "dxf", "sketch", "feature", "extrude", "cad"],
    "fea": ["fea", "simulation", "ansys", "static", "modal", "buckling", "mesh", "boundary", "contact", "convergence", "finite element", "stress plot", "load case"],
    "cfd": ["cfd", "fluent", "flow", "thermal", "heat", "pressure drop", "reynolds", "turbulence", "y+", "convection", "fluid", "pipe", "velocity", "cooling"],
    "manufacturing": ["dfm", "dfa", "manufacturing", "injection", "molding", "moulding", "machining", "sheet metal", "tooling", "cycle time", "scrap", "assembly", "cost", "weld line", "sink", "warpage", "draft"],
    "materials": ["material", "materials", "ashby", "asm", "steel", "aluminum", "plastic", "abs", "pc", "pp", "nylon", "pa", "peek", "strength", "stiffness", "density", "corrosion", "datasheet"],
    "patent": ["patent", "prior art", "claim", "innovation", "invention", "triz", "novelty", "prototype", "wipo", "uspto"],
}

ONTOLOGY: Dict[str, List[str]] = {
    "injection molded cover": ["function", "material family", "wall thickness", "draft", "ribs", "bosses", "shrinkage", "sink marks", "warpage", "gate location", "ejector marks", "surface class", "snap-fit/screws", "tolerance class", "tooling cost", "cycle time", "validation samples"],
    "shaft": ["torque", "bending moment", "combined stress", "fatigue", "keyway", "bearing seats", "stress concentration", "deflection", "critical speed", "material", "surface finish", "heat treatment"],
    "bracket": ["load path", "constraint realism", "material", "ribbing", "fillets", "bolt pattern", "stress concentration", "manufacturing process", "FEA validation", "safety factor"],
    "pipe flow": ["fluid", "density", "viscosity", "diameter", "velocity", "Reynolds number", "friction factor", "pressure drop", "roughness", "minor losses", "temperature"],
    "sheet metal": ["thickness", "bend radius", "K-factor", "grain direction", "relief", "hole-to-bend distance", "flat pattern", "springback", "tooling"],
    "cad macro": ["document type", "selection manager", "feature manager", "sketch plane", "units", "rebuild", "file overwrite risk", "export path", "error handling"],
}

PROTOCOLS: Dict[str, List[str]] = {
    "chief": [
        "Define engineering objective and decision needed.",
        "Identify function, constraints, loads, material, process, environment, and verification method.",
        "Retrieve internal workspace knowledge and apply only relevant rules.",
        "State assumptions, missing data, risk level, and next action.",
    ],
    "mechanical": [
        "Define function, loads, supports, geometry, material, environment, and life requirement.",
        "Identify likely failure modes: yielding, fatigue, deflection, buckling, wear, thermal distortion.",
        "Run hand/sanity calculations before detailed CAD or simulation.",
        "Check manufacturability, tolerance stack-up, assembly, and validation test plan.",
    ],
    "manufacturing": [
        "Identify process family and production volume.",
        "Map geometry to process capability and tooling constraints.",
        "Check tolerance feasibility, cycle time, scrap risk, inspection burden, and assembly effort.",
        "Rank design changes by manufacturability impact and cost reduction potential.",
    ],
    "materials": [
        "Translate function into material requirements.",
        "Compare stiffness, strength, toughness, density, temperature, corrosion, processing, cost, and availability.",
        "Reject materials that fail environment, process, or supply constraints.",
        "Require datasheet confirmation before release.",
    ],
    "fea": [
        "Define the simulation question and acceptance criterion.",
        "Check load path, constraints, contacts, material model, and mesh strategy.",
        "Perform mesh convergence and compare with hand calculation or benchmark.",
        "Interpret stress plots only after setup verification.",
    ],
    "cfd": [
        "Define flow domain, objective, fluid properties, and boundary conditions.",
        "Estimate Reynolds number and select laminar/turbulence model accordingly.",
        "Check mesh quality, y plus target, convergence, and conservation balances.",
        "Validate against analytical pressure drop, heat transfer estimate, or test data.",
    ],
    "solidworks": [
        "Clarify document type, units, target geometry, and output files.",
        "Separate sketch creation, feature creation, drawings, BOM, export, and error handling.",
        "Protect user files from destructive overwrite.",
        "Explain how to run and validate the automation.",
    ],
    "patent": [
        "Separate problem, inventive concept, implementation, and measurable advantage.",
        "Search prior art before deep investment.",
        "Convert concept into testable prototype requirements and claim-like elements.",
        "Avoid legal certainty without patent attorney review.",
    ],
}

DEFAULT_PACKS: Dict[str, Dict[str, object]] = {
    "mechanical_design": {
        "title": "Mechanical Design",
        "refs": ["Shigley methodology", "Roark methodology", "Machinery Handbook practice", "ASME Y14.5 GD&T logic", "systems engineering validation thinking"],
        "rules": [
            "Define loads, constraints, materials, environment, safety factor, and validation method before design release.",
            "Check manufacturability, tolerance stack-up, failure modes, assembly risk, and test plan before final design.",
            "Use hand calculations as sanity checks before simulation or detailed CAD decisions.",
            "Separate unknown assumptions from confirmed inputs.",
        ],
    },
    "cad_solidworks": {
        "title": "CAD / SolidWorks",
        "refs": ["SolidWorks API methodology", "VBA macro patterns", "engineering drawing practice", "STEP/DXF export workflows"],
        "rules": [
            "Prefer parametric, editable CAD models with clear dimensions and feature names.",
            "Separate geometry creation, features, drawings, BOM, and exports.",
            "Warn before destructive macros or file overwrites.",
            "Every automation needs a verification step after rebuild/export.",
        ],
    },
    "simulation_fea": {
        "title": "Simulation / FEA",
        "refs": ["FEA verification and validation methodology", "ANSYS setup logic", "NAFEMS-style model credibility", "mesh convergence practice"],
        "rules": [
            "Define the simulation objective and acceptance criterion before setup.",
            "Check load paths, constraints, contacts, material model, mesh quality, and convergence.",
            "Validate FEA with hand calculations, test data, or benchmark cases.",
            "Treat stress plots as evidence only after model verification.",
        ],
    },
    "cfd_thermal": {
        "title": "CFD / Thermal",
        "refs": ["CFD finite volume methodology", "Fluent theory logic", "heat transfer fundamentals", "fluid mechanics pressure-drop logic"],
        "rules": [
            "Identify flow regime using Reynolds number before model selection.",
            "Check boundary conditions, mesh quality, y plus, convergence, and conservation balances.",
            "Validate CFD with analytical estimates or experimental data.",
            "Separate physical modeling uncertainty from numerical error.",
        ],
    },
    "manufacturing_dfm": {
        "title": "Manufacturing / DFM",
        "refs": ["manufacturing process selection methodology", "DFA/DFM logic", "injection molding design guidance", "sheet metal and machining design practice"],
        "rules": [
            "Match geometry to manufacturing process capability.",
            "Avoid unnecessary tight tolerances.",
            "Consider tooling, cycle time, scrap, inspection, assembly, and repeatability.",
            "Design for production stability, not prototype success only.",
        ],
    },
    "materials_selection": {
        "title": "Materials Selection",
        "refs": ["Ashby-style selection logic", "ASM-style material property reasoning", "supplier datasheet confirmation", "process compatibility screening"],
        "rules": [
            "Start from functional requirements, not material preference.",
            "Compare stiffness, strength, toughness, density, thermal limits, corrosion, process compatibility, cost, and availability.",
            "Never select a material from strength alone.",
            "Always check manufacturing compatibility and supplier availability.",
        ],
    },
    "innovation_patent": {
        "title": "Innovation / Patent",
        "refs": ["TRIZ contradiction thinking", "prior-art search logic", "prototype validation planning", "claim drafting checklist logic"],
        "rules": [
            "Separate novelty, usefulness, manufacturability, and commercial value.",
            "Search prior art before heavy development investment.",
            "Convert ideas into testable claims and prototype requirements.",
            "Avoid giving legal certainty without patent attorney review.",
        ],
    },
}

DETAILED_PACKS: Dict[str, Dict[str, str]] = {
    "manufacturing_dfm": {
        "injection_molding.md": """# Injection Molding DFM Protocol

Concept:
Injection molding design must balance geometry, material, tooling, cooling, ejection, surface class, dimensional tolerance, and production volume.

Rules:
- Keep nominal wall thickness as uniform as possible.
- Avoid abrupt thick-to-thin transitions; they increase sink, voids, warpage, and differential cooling.
- Add draft on vertical faces, ribs, bosses, and shutoff surfaces.
- Use ribs for stiffness instead of thick solid sections.
- Bosses should be cored and supported with ribs where needed.
- Add radii to improve flow and reduce stress concentration.
- Reserve realistic gate, ejector, parting line, and shutoff locations early.
- Avoid tight tolerances unless function requires them.

Required inputs:
- Material grade, nominal wall thickness, CAD/STEP, production volume, surface class, assembly method, critical dimensions, environment.

Failure risks:
- Sink marks, warpage, weld lines, short shots, trapped air, ejection marks, excessive cycle time, expensive tooling changes.
""",
        "sheet_metal.md": """# Sheet Metal DFM Protocol

Rules:
- Match bend radius to material thickness and tooling.
- Keep holes and slots away from bend lines.
- Add bend relief where tearing or distortion is likely.
- Simplify bend sequence to reduce setup time.
- Confirm flat pattern, K-factor, grain direction, and finish requirement.

Required inputs:
- Material, thickness, bend radius, bend count, hole positions, tolerance class, surface finish, annual volume.
""",
        "machining.md": """# Machining DFM Protocol

Rules:
- Reduce deep pockets, sharp internal corners, unnecessary tight tolerances, and excessive setups.
- Use standard tool sizes and accessible features.
- Define datums that match workholding and inspection.
- Separate prototype-friendly choices from production-stable choices.

Cost drivers:
- Setup count, tool changes, tolerance tightness, material machinability, surface finish, inspection burden, scrap risk.
""",
        "assembly_dfa.md": """# Assembly DFA Protocol

Rules:
- Reduce part count and fastener count.
- Design self-locating and mistake-proofed features.
- Keep assembly direction simple.
- Avoid hidden fasteners and inaccessible clips.
- Define datum scheme and inspection points.
""",
        "tolerance_process_capability.md": """# Tolerance and Process Capability Protocol

Rules:
- Tight tolerances must be linked to function.
- Match tolerance class to process capability.
- Review tolerance stack-up for assemblies.
- Avoid cosmetic or arbitrary precision requirements.
- Define inspection method before release.
""",
        "injection_molding_expert.md": """# Injection Molding Expert DFM Pack

Concept:
Injection molding is a coupled design/manufacturing problem. Geometry, material, tooling, cooling, ejection, surface quality, tolerance capability, and production volume must be considered together.

Rules:
- Confirm material family and grade before final wall thickness, shrinkage, draft, and tolerance decisions.
- Keep wall thickness uniform; avoid thick masses and abrupt transitions.
- Add draft to all pull-direction surfaces; textured surfaces need more draft.
- Use ribs for stiffness instead of thick sections; avoid overly thick rib roots.
- Core bosses and support them with ribs; avoid isolated thick bosses.
- Add generous radii to support flow, reduce stress concentration, and improve tool life.
- Reserve gate, runner, ejector, parting-line, and shutoff strategy before design freeze.
- Protect cosmetic A-surfaces from gates, ejector pins, sink, weld lines, and parting-line mismatch.
- Avoid tight plastic tolerances unless tied to functional datums and realistic process capability.
- Plan prototype, T0/T1 sampling, dimensional inspection, and functional validation.

Decision logic:
- If wall thickness is unknown, do not approve DFM; request nominal wall map.
- If material is unknown, identify candidate material family and grade-level risks.
- If annual volume is low, question whether injection tooling is economically justified.
- If cosmetic surface is critical, gate/ejector/parting-line placement becomes release-critical.

Failure risks:
- Sink marks, voids, short shot, weld line weakness, warpage, differential shrinkage, flash, ejection damage, brittle snaps, dimensional drift, high cycle time.

Required inputs:
- CAD/STEP or image, material grade, nominal wall thickness, surface class, production volume, assembly method, critical dimensions, tolerance requirements, operating environment.
""",
        "sheet_metal_expert.md": """# Sheet Metal Expert DFM Pack

Rules:
- Match bend radius, material thickness, tooling, and material ductility.
- Keep holes, slots, embosses, and cutouts away from bend lines.
- Add bend relief where tearing, bulging, or distortion is likely.
- Minimize bend setups and complex forming directions.
- Define grain direction, flat pattern, K-factor, finish side, and burr direction.
- Avoid tight flatness/perpendicularity without process capability evidence.

Decision logic:
- If bend count is high, review sequence, tooling availability, and accumulated tolerance.
- If holes are near bends, request hole-to-bend distances and tooling review.
- If cosmetic finish matters, specify protected face and handling requirements.
""",
        "machining_expert.md": """# Machining Expert DFM Pack

Rules:
- Reduce setups, deep pockets, long-reach tools, thin walls, sharp internal corners, and unnecessary tight tolerances.
- Prefer standard cutter sizes, standard hole sizes, accessible features, and stable workholding.
- Define datums that match fixturing and inspection.
- Separate prototype-friendly machining from production-stable machining.
- Link surface finish and tolerance to functional requirements.

Cost drivers:
- Setup count, tool changes, deep cavities, material machinability, tight tolerances, fine surface finish, inspection burden, scrap risk, deburring, and secondary operations.
""",
        "assembly_dfa_expert.md": """# Assembly DFA Expert Pack

Rules:
- Reduce part count and fastener count where function allows.
- Use self-locating, self-aligning, and mistake-proofed features.
- Keep assembly direction simple and visible.
- Avoid hidden fasteners, inaccessible clips, and ambiguous orientation.
- Design datums, stops, lead-ins, and inspection features into the product.
- Review serviceability, tool access, and rework risk.

Decision logic:
- If assembly method is unknown, do not finalize snap fits, bosses, inserts, or fastener strategy.
- If tolerance stack affects assembly, request datum scheme and critical dimensions.
""",
        "tolerance_capability_expert.md": """# Tolerance Capability Expert Pack

Rules:
- Every tight tolerance must have a functional reason.
- Match tolerances to process capability, measurement method, and production volume.
- Review tolerance stack-up for mating parts and assembly function.
- Avoid mixing cosmetic expectations with functional precision.
- Define inspection strategy before design release.
- For plastics, account for shrinkage, moisture, temperature, part aging, and mold cavity variation.

Decision logic:
- If tolerance is tighter than normal process capability, propose datum change, feature redesign, secondary operation, or inspection plan.
""",
        "cost_reduction_expert.md": """# Manufacturing Cost-Down Expert Pack

Rules:
- Identify cost drivers before suggesting redesign.
- Reduce material volume, cycle time, setup count, part count, fasteners, inspection effort, and scrap risk.
- Prefer geometry simplification over late-stage process heroics.
- Avoid excessive tolerances, secondary operations, and cosmetic requirements without value justification.
- Consider supplier tooling, standard stock/forms, cavity count, and packaging/handling.

Cost-down levers:
- Part consolidation, wall-thickness optimization, ribbing instead of mass, simplified tooling, standard fasteners, datum simplification, reduced inspection, common material grades, and fewer finishing operations.
""",
        "quality_control_expert.md": """# Manufacturing Quality Control Expert Pack

Rules:
- Define CTQs: critical-to-quality dimensions, cosmetic zones, functional interfaces, and safety-related checks.
- Link inspection method to tolerance and production volume.
- Separate incoming material checks, in-process checks, final inspection, and validation tests.
- Use control plans for high-volume production.
- Track defect modes: sink, flash, warpage, short shot, weld-line weakness, burrs, dimensional drift, assembly force, and cosmetic damage.

Validation:
- Use first article inspection, capability checks, functional tests, environmental exposure, and pilot build feedback before release.
""",
    },
    "simulation_fea": {
        "static_structural.md": """# Static Structural FEA Protocol

Rules:
- Define objective and acceptance criterion before building the model.
- Use realistic boundary conditions that preserve the real load path.
- Check contacts, stiffness assumptions, material model, and mesh convergence.
- Compare reaction forces with applied loads.
- Validate peak stress interpretation near singularities.
""",
        "mesh_convergence.md": """# Mesh Convergence Protocol

Rules:
- Refine mesh around stress gradients, contacts, holes, fillets, and load introduction areas.
- Track displacement, reaction force, and stress away from singularities.
- Do not trust a single mesh result.
""",
    },
    "cfd_thermal": {
        "internal_flow.md": """# Internal Flow CFD Protocol

Rules:
- Compute Reynolds number before choosing laminar or turbulent model.
- Define inlet, outlet, wall, temperature, and roughness assumptions.
- Check mass balance and pressure drop against analytical estimates.
- Use inflation layers when wall shear or heat transfer matters.
""",
        "heat_transfer.md": """# Heat Transfer Reasoning Protocol

Rules:
- Separate conduction, convection, radiation, and contact resistance.
- Estimate heat load and thermal resistance network before CFD.
- Validate temperature predictions with simplified calculations or test data.
""",
    },
    "materials_selection": {
        "thermoplastics.md": """# Thermoplastics Selection Protocol

Rules:
- ABS: useful for general covers, cosmetics, and moderate impact, but verify temperature and chemical exposure.
- PP: low density and chemical resistance, but lower stiffness and higher shrinkage risk.
- PC: higher impact and transparency options, but stress cracking and processing must be checked.
- PA/Nylon: good toughness and wear, but moisture absorption affects dimensions.
- Always verify grade-specific datasheets before release.
""",
    },
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
    raw_excerpt: str

@dataclass
class QueryFrame:
    agent: str
    part_type: str
    process: str
    materials: List[str]
    quantities: List[str]
    concepts: List[str]
    missing_data: List[str]
    confidence: str

# -----------------------------------------------------------------------------
# Knowledge files
# -----------------------------------------------------------------------------
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
    for pack, files in DETAILED_PACKS.items():
        p = KNOWLEDGE_DIR / pack
        p.mkdir(parents=True, exist_ok=True)
        for filename, text in files.items():
            target = p / filename
            if not target.exists():
                target.write_text(text.strip() + "\n", encoding="utf-8")

def clean_md(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r'[#*_`>"]', " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_bullets(text: str, section: str) -> List[str]:
    lines = text.splitlines()
    active = False
    out: List[str] = []
    target = section.strip().lower()
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

def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(APP_DIR)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def load_docs() -> List[KnowledgeDoc]:
    seed_knowledge_packs()
    docs: List[KnowledgeDoc] = []
    for md in sorted(KNOWLEDGE_DIR.glob("**/*.md")):
        pack = md.relative_to(KNOWLEDGE_DIR).parts[0]
        raw = md.read_text(encoding="utf-8", errors="ignore")
        refs = extract_bullets(raw, "Core references") or list(DEFAULT_PACKS.get(pack, {}).get("refs", []))
        rules = extract_bullets(raw, "Engineering rules") or extract_bullets(raw, "Rules") or list(DEFAULT_PACKS.get(pack, {}).get("rules", []))
        docs.append(KnowledgeDoc(pack=pack, title=pack_display_name(pack), path=relative_path(md), refs=refs, rules=rules, raw=raw))
    return docs

# -----------------------------------------------------------------------------
# Routing + retrieval
# -----------------------------------------------------------------------------
def tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9\+\#\.\-/]+|[\u0600-\u06FF]+", text.lower())

def infer_agent(query: str) -> str:
    q = query.lower()
    best_agent = "chief"
    best_score = 0
    for agent, words in INTENT_KEYWORDS.items():
        score = 0
        for w in words:
            if w in q:
                score += 4 if " " in w else 1
        if score > best_score:
            best_score = score
            best_agent = agent
    return best_agent

def route_agent(query: str, selected_workspace: str) -> str:
    inferred = infer_agent(query)
    if inferred != "chief":
        return inferred
    return selected_workspace or "chief"

def retrieve_knowledge(query: str, agent: str, top_k: int = 4) -> List[KnowledgeHit]:
    docs = load_docs()
    q = query.lower()
    q_tokens = set(tokens(query))
    preferred_pack = WORKSPACE_TO_PACK.get(agent, "")
    inferred_pack = WORKSPACE_TO_PACK.get(infer_agent(query), "")
    hits: List[KnowledgeHit] = []
    for doc in docs:
        searchable = clean_md(doc.raw + " " + " ".join(doc.refs) + " " + " ".join(doc.rules))
        raw_tokens = set(tokens(searchable))
        score = float(len(q_tokens & raw_tokens))
        filename = Path(doc.path).name.lower()
        # Domain phrase boosts.
        if any(x in q for x in ["injection", "mold", "mould", "dfm", "dfa", "tooling", "sink", "warpage"]):
            if doc.pack == "manufacturing_dfm": score += 12
            if filename == "injection_molding.md": score += 18
            if doc.pack == "materials_selection": score += 6
        if any(x in q for x in ["abs", "pp", "pc", "nylon", "pa", "plastic", "polymer", "thermoplastic"]):
            if doc.pack == "materials_selection": score += 10
            if filename == "thermoplastics.md": score += 12
        if any(x in q for x in ["solidworks", "macro", "vba", "step", "dxf", "cad"]):
            if doc.pack == "cad_solidworks": score += 14
        if any(x in q for x in ["fea", "ansys", "mesh", "stress", "modal", "buckling"]):
            if doc.pack == "simulation_fea": score += 14
        if any(x in q for x in ["cfd", "flow", "thermal", "heat", "reynolds", "pressure drop", "fluid"]):
            if doc.pack == "cfd_thermal": score += 14
        if any(x in q for x in ["shaft", "bearing", "gear", "spring", "bracket", "load", "fatigue"]):
            if doc.pack == "mechanical_design": score += 10
        if any(x in q for x in ["patent", "innovation", "invention", "claim", "prior art"]):
            if doc.pack == "innovation_patent": score += 14
        if preferred_pack and doc.pack == preferred_pack:
            score *= 1.2
        if inferred_pack and doc.pack == inferred_pack:
            score *= 1.3
        if score > 0:
            excerpt = clean_md(doc.raw)[:420]
            hits.append(KnowledgeHit(doc.pack, doc.title, doc.path, round(score, 3), doc.refs[:4], doc.rules[:8], excerpt))
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:top_k]

# -----------------------------------------------------------------------------
# Reasoning frame + deterministic helpers
# -----------------------------------------------------------------------------
def infer_part_type(q: str) -> str:
    s = q.lower()
    if "cover" in s or "lid" in s: return "cover/enclosure"
    if "shaft" in s: return "shaft"
    if "bracket" in s: return "bracket"
    if "pipe" in s or "duct" in s: return "pipe/duct"
    if "gear" in s: return "gear"
    if "housing" in s: return "housing"
    return "unspecified component"

def infer_process(q: str, agent: str) -> str:
    s = q.lower()
    if "injection" in s or "mold" in s or "mould" in s: return "injection molding"
    if "sheet metal" in s or "bend" in s: return "sheet metal fabrication"
    if "machining" in s or "milling" in s or "turning" in s: return "machining"
    if agent == "manufacturing": return "manufacturing process not fully specified"
    return "not specified"

def extract_materials(q: str) -> List[str]:
    candidates = ["abs", "pp", "pc", "pa", "nylon", "peek", "aluminum", "aluminium", "steel", "stainless", "brass", "copper", "polycarbonate", "polypropylene"]
    s = q.lower()
    return sorted({c.upper() if c in ["abs", "pp", "pc", "pa", "peek"] else c.title() for c in candidates if c in s})

def extract_quantities(q: str) -> List[str]:
    # Captures simple values such as 2 mm, 500 N, 3 bar, 10k units/year.
    pattern = r"\b\d+(?:\.\d+)?\s*(?:mm|cm|m|n|kn|nm|mpa|gpa|bar|pa|kg|g|rpm|c|°c|w|kw|l/min|m/s|units/year|pcs|pieces|%)\b"
    return re.findall(pattern, q.lower())

def related_concepts(query: str) -> List[str]:
    q = query.lower()
    concepts: List[str] = []
    for key, values in ONTOLOGY.items():
        if any(part in q for part in key.split()) or key in q:
            concepts.extend(values)
    if "injection" in q or "mold" in q or "dfm" in q:
        concepts.extend(ONTOLOGY["injection molded cover"])
    return list(dict.fromkeys(concepts))[:18]

def missing_data_for(agent: str, process: str, part: str, materials: List[str], quantities: List[str]) -> List[str]:
    missing: List[str] = []
    if part == "unspecified component": missing.append("component function and part type")
    if not materials: missing.append("material family and grade")
    if not quantities: missing.append("key dimensions, loads, tolerances, or operating values")
    if agent == "manufacturing" or process == "injection molding":
        missing += ["CAD/STEP or image", "nominal wall thickness", "production volume", "surface/cosmetic class", "assembly method", "critical dimensions/tolerances"]
    if agent == "fea":
        missing += ["load cases", "constraints", "contacts", "material model", "acceptance criterion"]
    if agent == "cfd":
        missing += ["fluid properties", "flow rate or velocity", "domain geometry", "boundary conditions", "temperature/heat load"]
    if agent == "materials":
        missing += ["temperature range", "chemical exposure", "stiffness/strength target", "manufacturing process", "cost target"]
    return list(dict.fromkeys(missing))[:9]

def confidence_level(missing: List[str]) -> str:
    if len(missing) >= 6: return "Low-to-medium"
    if len(missing) >= 3: return "Medium"
    return "Medium-to-high"

def build_query_frame(query: str, agent: str) -> QueryFrame:
    part = infer_part_type(query)
    process = infer_process(query, agent)
    materials = extract_materials(query)
    quantities = extract_quantities(query)
    concepts = related_concepts(query)
    missing = missing_data_for(agent, process, part, materials, quantities)
    return QueryFrame(agent, part, process, materials, quantities, concepts, missing, confidence_level(missing))

def first_rules(hits: List[KnowledgeHit], pack: str, fallback: List[str], n: int = 5) -> List[str]:
    for h in hits:
        if h.pack == pack and h.rules:
            return h.rules[:n]
    return fallback[:n]

def sources_block(hits: List[KnowledgeHit]) -> str:
    if not hits:
        return "**Internal sources used**\n- No internal source matched strongly. Add a workspace note or source document."
    lines = ["**Internal sources used**"]
    seen = set()
    i = 1
    for h in hits:
        key = (h.pack, h.path)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- [K{i}] {h.title} — `{h.path}`")
        i += 1
    return "\n".join(lines)

def protocol_block(agent: str) -> str:
    steps = PROTOCOLS.get(agent, PROTOCOLS["chief"])
    return "**Reasoning protocol applied**\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))

def assumptions_block(frame: QueryFrame) -> str:
    mats = ", ".join(frame.materials) if frame.materials else "not specified"
    qty = ", ".join(frame.quantities) if frame.quantities else "not specified"
    concepts = ", ".join(frame.concepts[:9]) if frame.concepts else "objective-specific engineering factors"
    return (
        "**Problem frame**\n"
        f"- Part/component: {frame.part_type}.\n"
        f"- Process/physics: {frame.process}.\n"
        f"- Materials detected: {mats}.\n"
        f"- Quantities detected: {qty}.\n"
        f"- Key concepts considered: {concepts}.\n"
        f"- Confidence: {frame.confidence}, because several release-critical inputs are still missing."
    )

def missing_block(frame: QueryFrame) -> str:
    if not frame.missing_data:
        return "**Missing data**\n- No major missing data detected from the question, but release still needs validation evidence."
    return "**Missing data needed for a real engineering decision**\n" + "\n".join(f"- {m}" for m in frame.missing_data)

def compose_dfm_answer(query: str, frame: QueryFrame, hits: List[KnowledgeHit]) -> str:
    rules = first_rules(hits, "manufacturing_dfm", DEFAULT_PACKS["manufacturing_dfm"]["rules"], 8)
    material_note = "Material is unspecified; do not freeze shrinkage, wall thickness, draft, snap-fit behavior, or tolerance assumptions until material family and grade are known."
    if frame.materials:
        material_note = f"Detected material candidates: {', '.join(frame.materials)}. Verify grade datasheets before locking shrinkage, wall thickness, heat resistance, impact behavior, and tolerances."

    injection_focus = "injection" in query.lower() or "mold" in query.lower() or "mould" in query.lower() or frame.process == "injection molding"
    process_review = (
        "1. **Process feasibility:** injection molding is plausible for a cover only if production volume and tooling budget justify mold cost. Confirm annual volume, cavity strategy, cosmetic class, and expected cycle time.\n"
        "2. **Wall-thickness strategy:** create a wall-thickness map from CAD. Keep nominal thickness consistent; redesign thick islands, abrupt transitions, thick bosses, and heavy corners.\n"
        "3. **Draft / tool release:** check all pull-direction faces, ribs, bosses, snaps, shutoffs, and texture zones for draft. Lack of draft creates ejection, scuffing, and tooling risk.\n"
        "4. **Ribs, bosses, and stiffness:** use ribs and local structure instead of mass. Core bosses and connect them to walls/ribs only where load transfer is needed.\n"
        "5. **Gate, ejector, and parting-line logic:** reserve gate, runner, ejector, parting-line, and shutoff strategy before design freeze, especially for visible A-surfaces.\n"
        "6. **Shrinkage/warpage risk:** review asymmetric wall sections, large flat panels, unbalanced ribs, gate location, fiber orientation if reinforced, and cooling feasibility.\n"
        "7. **Tolerance capability:** separate functional dimensions from cosmetic dimensions. Avoid tight plastic tolerances unless process capability and inspection method are defined.\n"
        "8. **Assembly/DFA:** review snap-fits, screws, inserts, sealing features, datum scheme, assembly direction, tool access, and service/rework risk.\n"
        "9. **Quality plan:** define CTQs, first article inspection, cosmetic acceptance, dimensional checks, functional tests, and pilot build feedback.\n"
        "10. **Cost-down logic:** reduce material mass, cycle time, scrap, tooling complexity, secondary operations, inspection burden, and part/fastener count."
    ) if injection_focus else (
        "1. **Process feasibility:** identify the intended process and production volume before judging manufacturability.\n"
        "2. **Geometry-process fit:** map major geometry features to process limits, tooling access, tolerance capability, and inspection method.\n"
        "3. **Assembly and cost:** reduce part count, setup count, fasteners, secondary operations, scrap risk, and unnecessary precision."
    )

    return (
        "**Internal Knowledge Only — Manufacturing / DFM Expert Review v22**\n\n"
        + assumptions_block(frame) + "\n\n"
        + protocol_block("manufacturing") + "\n\n"
        "**Expert manufacturing assessment**\n"
        + process_review + "\n\n"
        f"**Material/process note**\n- {material_note}\n\n"
        "**Internal rules applied from Manufacturing / DFM Expert Pack**\n" + "\n".join(f"- {r}" for r in rules[:8]) + "\n\n"
        + missing_block(frame) + "\n\n"
        "**Recommended next action**\n"
        "- Provide CAD image/STEP, material grade, nominal wall thickness, annual production volume, surface class, assembly method, and critical tolerances. With those inputs, MechAI can produce a ranked DFM risk table and cost-down action list.\n\n"
        + sources_block(hits) + "\n\n"
        "**Engineering use note:** this is internal knowledge-pack guidance, not certified production approval. Validate tooling assumptions, dimensional capability, mold-flow risks, inspection plan, and test evidence before release."
    )

def compose_fea_answer(query: str, frame: QueryFrame, hits: List[KnowledgeHit]) -> str:
    rules = first_rules(hits, "simulation_fea", DEFAULT_PACKS["simulation_fea"]["rules"], 6)
    return (
        "**Internal Knowledge Only — FEA scientist setup review**\n\n"
        + assumptions_block(frame) + "\n\n"
        + protocol_block("fea") + "\n\n"
        "**Simulation setup checklist**\n"
        "1. Define the exact question: strength, stiffness, fatigue, buckling, modal response, or thermal stress.\n"
        "2. Identify real load paths and avoid artificial constraints that over-stiffen the model.\n"
        "3. Define material model, contacts, fasteners, and load introduction surfaces.\n"
        "4. Plan mesh refinement around holes, fillets, contacts, supports, and high gradients.\n"
        "5. Track convergence using displacement, reaction forces, and stress away from singularities.\n"
        "6. Compare results with hand calculations or a physical/benchmark test before design release.\n\n"
        "**Internal rules applied**\n" + "\n".join(f"- {r}" for r in rules) + "\n\n"
        + missing_block(frame) + "\n\n" + sources_block(hits)
    )

def compose_cfd_answer(query: str, frame: QueryFrame, hits: List[KnowledgeHit]) -> str:
    rules = first_rules(hits, "cfd_thermal", DEFAULT_PACKS["cfd_thermal"]["rules"], 6)
    return (
        "**Internal Knowledge Only — CFD / Thermal scientist review**\n\n"
        + assumptions_block(frame) + "\n\n"
        + protocol_block("cfd") + "\n\n"
        "**CFD/thermal setup checklist**\n"
        "1. Define the domain, fluid, flow rate/velocity, heat load, and boundary conditions.\n"
        "2. Estimate Reynolds number before choosing laminar or turbulent modeling.\n"
        "3. Decide whether wall heat transfer, pressure drop, mixing, or cooling uniformity is the main output.\n"
        "4. Use inflation layers where wall shear or heat transfer matters; define target y plus.\n"
        "5. Check mass/energy balance, residuals, monitored outputs, and mesh independence.\n"
        "6. Validate with pressure-drop or heat-transfer estimates before trusting detailed contours.\n\n"
        "**Internal rules applied**\n" + "\n".join(f"- {r}" for r in rules) + "\n\n"
        + missing_block(frame) + "\n\n" + sources_block(hits)
    )

def compose_materials_answer(query: str, frame: QueryFrame, hits: List[KnowledgeHit]) -> str:
    rules = first_rules(hits, "materials_selection", DEFAULT_PACKS["materials_selection"]["rules"], 6)
    return (
        "**Internal Knowledge Only — Materials selection scientist review**\n\n"
        + assumptions_block(frame) + "\n\n"
        + protocol_block("materials") + "\n\n"
        "**Selection logic**\n"
        "1. Convert the function into measurable requirements: stiffness, strength, impact, temperature, chemical exposure, density, finish, and cost.\n"
        "2. Screen out materials that fail environment, manufacturing process, or supplier availability.\n"
        "3. Compare candidates by property trade-offs, not by one property alone.\n"
        "4. Confirm actual grade datasheets before release.\n\n"
        "**Internal rules applied**\n" + "\n".join(f"- {r}" for r in rules) + "\n\n"
        + missing_block(frame) + "\n\n" + sources_block(hits)
    )

def compose_cad_answer(query: str, frame: QueryFrame, hits: List[KnowledgeHit]) -> str:
    rules = first_rules(hits, "cad_solidworks", DEFAULT_PACKS["cad_solidworks"]["rules"], 6)
    return (
        "**Internal Knowledge Only — CAD / SolidWorks reasoning**\n\n"
        + assumptions_block(frame) + "\n\n"
        + protocol_block("solidworks") + "\n\n"
        "**CAD automation structure**\n"
        "1. Clarify part/assembly/drawing context and units.\n"
        "2. Define parameters and feature tree before writing automation.\n"
        "3. Separate sketch creation, feature creation, drawing/BOM, export, and error handling.\n"
        "4. Include validation after rebuild and before file export.\n\n"
        "**Internal rules applied**\n" + "\n".join(f"- {r}" for r in rules) + "\n\n" + sources_block(hits)
    )

def compose_mechanical_answer(query: str, frame: QueryFrame, hits: List[KnowledgeHit]) -> str:
    rules = first_rules(hits, "mechanical_design", DEFAULT_PACKS["mechanical_design"]["rules"], 6)
    return (
        "**Internal Knowledge Only — Mechanical design scientist review**\n\n"
        + assumptions_block(frame) + "\n\n"
        + protocol_block("mechanical") + "\n\n"
        "**Design reasoning checklist**\n"
        "1. Define function, load cases, constraints, duty cycle, and environment.\n"
        "2. Identify likely failure modes: yielding, fatigue, buckling, deflection, wear, creep, thermal distortion.\n"
        "3. Use first-principles estimates before detailed CAD or simulation.\n"
        "4. Check material/process compatibility, tolerance stack-up, assembly, and validation tests.\n\n"
        "**Internal rules applied**\n" + "\n".join(f"- {r}" for r in rules) + "\n\n"
        + missing_block(frame) + "\n\n" + sources_block(hits)
    )

def compose_patent_answer(query: str, frame: QueryFrame, hits: List[KnowledgeHit]) -> str:
    rules = first_rules(hits, "innovation_patent", DEFAULT_PACKS["innovation_patent"]["rules"], 6)
    return (
        "**Internal Knowledge Only — Innovation / patent reasoning**\n\n"
        + assumptions_block(frame) + "\n\n"
        + protocol_block("patent") + "\n\n"
        "**Innovation analysis**\n"
        "1. Define the technical problem and current alternatives.\n"
        "2. State the inventive mechanism, not just the product idea.\n"
        "3. Identify measurable advantage: cost, performance, reliability, ease of manufacturing, or user benefit.\n"
        "4. Convert the idea into prototype requirements and prior-art search keywords.\n\n"
        "**Internal rules applied**\n" + "\n".join(f"- {r}" for r in rules) + "\n\n"
        "Not legal advice. Use a patent attorney for filing decisions.\n\n" + sources_block(hits)
    )

def compose_chief_answer(query: str, frame: QueryFrame, hits: List[KnowledgeHit]) -> str:
    rules: List[str] = []
    for h in hits:
        rules.extend(h.rules[:2])
    if not rules:
        rules = DEFAULT_PACKS["mechanical_design"]["rules"][:3]
    return (
        "**Internal Knowledge Only — Chief Mechanical Scientist starting point**\n\n"
        + assumptions_block(frame) + "\n\n"
        + protocol_block("chief") + "\n\n"
        "**Initial engineering reasoning**\n"
        + "\n".join(f"- {r}" for r in list(dict.fromkeys(rules))[:7]) + "\n\n"
        + missing_block(frame) + "\n\n" + sources_block(hits)
    )

def compose_answer(query: str, agent: str, hits: List[KnowledgeHit]) -> str:
    frame = build_query_frame(query, agent)
    if agent == "manufacturing": return compose_dfm_answer(query, frame, hits)
    if agent == "fea": return compose_fea_answer(query, frame, hits)
    if agent == "cfd": return compose_cfd_answer(query, frame, hits)
    if agent == "materials": return compose_materials_answer(query, frame, hits)
    if agent == "solidworks": return compose_cad_answer(query, frame, hits)
    if agent == "mechanical": return compose_mechanical_answer(query, frame, hits)
    if agent == "patent": return compose_patent_answer(query, frame, hits)
    return compose_chief_answer(query, frame, hits)

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
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3{font-size:18px!important;line-height:1.75!important;margin:0!important;}
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
if "project" not in st.session_state:
    st.session_state.project = "RD_Lab"

# Remove old raw/AI messages from prior builds.
def old_message(m: dict) -> bool:
    c = str(m.get("content", ""))
    bad = ["provider failed", "Internal knowledge retrieved:", "Knowledge Pack ##", "AI Provider", "API_KEY"]
    return any(b in c for b in bad)
if any(old_message(m) for m in st.session_state.messages):
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
    idx = ws_keys.index(st.session_state.workspace) if st.session_state.workspace in ws_keys else 0
    selected_label = st.selectbox("Workspace", ws_labels, index=idx, label_visibility="collapsed")
    st.session_state.workspace = ws_keys[ws_labels.index(selected_label)]
    st.markdown('<div class="note">Workspace biases the internal mechanical brain. Auto-routing still reads the question.</div>', unsafe_allow_html=True)

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
        st.caption("Brain: Mechanical Scientist v22 · DFM Expert Pack")
        st.caption(f"Internal knowledge docs: {len(load_docs())}")
        st.caption(f"Reasoning protocols: {len(PROTOCOLS)}")
        st.caption("External providers are not part of this build.")
        st.caption(f"Build: {BUILD_ID}")
    st.markdown('<div class="user-chip">Wafeeq · MechAI Pro</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if st.session_state.view == "About":
    st.markdown(f"""
**MechAI Pro — Mechanical Scientist Brain v22**

This build uses an internal mechanical reasoning engine:

- Engineering ontology: part → function → material → process → failure modes → validation.
- Reasoning protocols for DFM, FEA, CFD, materials, CAD, mechanical design, and innovation.
- Internal `knowledge_packs` are the reference brain.
- External AI providers are not part of this build.

**Build:** `{BUILD_ID}`

**v22 focus:** Manufacturing / DFM Expert Pack with injection molding, sheet metal, machining, DFA, tolerance capability, cost-down, and quality-control reasoning.

Public demo warning: verify calculations, CAD scripts, simulations, standards compliance, and safety-critical decisions before engineering use.
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
                st.markdown(f'<div class="message-row"><div class="avatar ai">⚙</div><div class="bubble ai"><div class="agent-tag">{html.escape(AGENTS.get(agent, AGENTS["chief"]))} · Internal Knowledge Only · Mechanical Scientist Brain v22</div>', unsafe_allow_html=True)
                st.markdown(content)
                st.markdown('</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="footer-note">MechAI Pro · Mechanical Scientist Brain v22 v22 · DFM Expert Pack · Verify all outputs before engineering use</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Execute
# -----------------------------------------------------------------------------
user_prompt = st.chat_input("Ask anything engineering…")
if user_prompt:
    selected_ws = st.session_state.workspace
    agent = route_agent(user_prompt, selected_ws)
    hits = retrieve_knowledge(user_prompt, agent, top_k=4)
    answer = compose_answer(user_prompt, agent, hits)
    st.session_state.messages.append({"role": "user", "content": user_prompt, "agent": agent})
    st.session_state.messages.append({"role": "assistant", "content": answer, "agent": agent})
    st.rerun()
