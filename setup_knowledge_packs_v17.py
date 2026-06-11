# -*- coding: utf-8 -*-
"""
Setup MechAI Pro v17 Knowledge Packs.
Run from the Mechanical_AI project folder:
    py setup_knowledge_packs_v17.py
"""

from pathlib import Path
import json

PACKS = {
    "mechanical_design": {
        "title": "Mechanical Design",
        "refs": [
            "Shigley's Mechanical Engineering Design",
            "Roark's Formulas for Stress and Strain",
            "Machinery's Handbook",
            "ASME Y14.5 GD&T principles",
            "NASA Systems Engineering Handbook",
        ],
        "rules": [
            "Define loads, constraints, materials, environment, safety factor, and validation method.",
            "Check manufacturability, tolerance stack-up, failure modes, and test plan before final design.",
            "Use hand calculations as sanity checks before simulation.",
        ],
    },
    "cad_solidworks": {
        "title": "CAD / SolidWorks",
        "refs": [
            "SolidWorks API Help",
            "SolidWorks VBA macro examples",
            "Engineering drawing standards",
            "STEP/DXF export practices",
        ],
        "rules": [
            "Prefer parametric, editable CAD models.",
            "Separate geometry creation, features, drawings, BOM, and exports.",
            "Warn before destructive macros or file overwrites.",
            "For macros, always explain how to run the macro and what SolidWorks objects it modifies.",
        ],
    },
    "simulation_fea": {
        "title": "Simulation / FEA",
        "refs": [
            "ANSYS Theory Reference",
            "NAFEMS verification and validation principles",
            "Cook: Concepts and Applications of Finite Element Analysis",
            "Practical FEA best practices",
        ],
        "rules": [
            "Define the simulation objective before setup.",
            "Check load paths, constraints, contacts, mesh quality, and convergence.",
            "Validate FEA with hand calculations, test data, or benchmark cases.",
            "Do not trust stress plots before checking assumptions, boundary conditions, and mesh convergence.",
        ],
    },
    "cfd_thermal": {
        "title": "CFD / Thermal",
        "refs": [
            "Versteeg and Malalasekera: An Introduction to CFD",
            "ANSYS Fluent Theory Guide",
            "Incropera: Fundamentals of Heat and Mass Transfer",
            "Fox and McDonald: Fluid Mechanics",
            "White: Fluid Mechanics",
        ],
        "rules": [
            "Identify flow regime using Reynolds number before model selection.",
            "Check boundary conditions, mesh quality, y plus, convergence, and conservation balances.",
            "Validate CFD with analytical estimates or experimental data.",
            "Separate physical modeling uncertainty from numerical error.",
        ],
    },
    "manufacturing_dfm": {
        "title": "Manufacturing / DFM",
        "refs": [
            "Kalpakjian: Manufacturing Engineering and Technology",
            "SME Manufacturing Engineering Handbook",
            "Boothroyd Dewhurst DFA/DFM methodology",
            "Injection molding design guides",
            "Sheet metal and machining design guides",
        ],
        "rules": [
            "Match geometry to manufacturing process capability.",
            "Avoid unnecessary tight tolerances.",
            "Consider tooling, cycle time, scrap, inspection, assembly, and repeatability.",
            "Design for production stability, not prototype success only.",
        ],
    },
    "materials_selection": {
        "title": "Materials Selection",
        "refs": [
            "Ashby: Materials Selection in Mechanical Design",
            "ASM Handbooks",
            "Supplier datasheets",
            "MatWeb-style material datasheet reasoning",
        ],
        "rules": [
            "Start from functional requirements, not material preference.",
            "Compare stiffness, strength, toughness, density, thermal limits, corrosion, process compatibility, cost, and availability.",
            "Never select a material from strength alone.",
            "Always check manufacturing compatibility and supplier availability.",
        ],
    },
    "innovation_patent": {
        "title": "Innovation / Patent",
        "refs": [
            "TRIZ methodology",
            "WIPO prior-art search approach",
            "USPTO classification logic",
            "Prototype validation planning",
            "Patent claim drafting checklists",
        ],
        "rules": [
            "Separate novelty, usefulness, manufacturability, and commercial value.",
            "Search prior art before heavy development investment.",
            "Convert ideas into testable claims and prototype requirements.",
            "Avoid giving legal certainty without patent attorney review.",
        ],
    },
}

def make_notes(data: dict) -> str:
    lines = [f"# {data['title']} Knowledge Pack", "", "## Core references"]
    lines.extend([f"- {r}" for r in data["refs"]])
    lines.extend(["", "## Engineering rules"])
    lines.extend([f"- {r}" for r in data["rules"]])
    lines.extend([
        "",
        "## Usage",
        "This pack is an internal MechAI Pro reference layer. Add legal PDFs, datasheets, company notes, standards excerpts, and catalogs inside `source_docs/`.",
        "",
        "Important: commercial textbooks and standards should not be copied into a public repository unless you have the right to distribute them.",
        ""
    ])
    return "\n".join(lines)

def main():
    base = Path("knowledge_packs")
    base.mkdir(exist_ok=True)

    for slug, data in PACKS.items():
        folder = base / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "source_docs").mkdir(exist_ok=True)
        (folder / "notes.md").write_text(make_notes(data), encoding="utf-8")
        (folder / "manifest.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print("OK: created/updated", len(PACKS), "knowledge packs.")
    print("Next check:")
    print("  Get-ChildItem knowledge_packs -Recurse -Filter notes.md")

if __name__ == "__main__":
    main()
