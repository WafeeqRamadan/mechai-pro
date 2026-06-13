
# -*- coding: utf-8 -*-
"""
MechAI Pro v23 — Mechanical Decision Engine
- Internal Knowledge Only.
- Implements 5 core pillars in one build:
  1) Deep Knowledge Packs for all workspaces
  2) Real Reasoning / Decision Engine
  3) Scoring Engines
  4) Engineering Calculators / validators
  5) Improved Retrieval Engine with chunking, metadata, ranking, citations, and confidence
Run: streamlit run app.py
"""
from __future__ import annotations

import html
import math
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import streamlit as st

APP_DIR = Path(__file__).parent
KNOWLEDGE_DIR = APP_DIR / "knowledge_packs"
BUILD_ID = "V23_MECHANICAL_DECISION_ENGINE_2026_06_13"

# =============================================================================
# Workspace definitions
# =============================================================================
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
}

INTENT_KEYWORDS = {
    "mechanical": ["design", "shaft", "bearing", "spring", "gear", "stress", "fatigue", "load", "safety factor", "tolerance", "gd&t", "mechanism", "bracket", "housing", "beam", "deflection", "bolt", "fastener", "fit"],
    "solidworks": ["solidworks", "macro", "vba", "api", "part", "assembly", "drawing", "bom", "step", "dxf", "sketch", "feature", "extrude", "cad", "swp", "sldprt"],
    "fea": ["fea", "simulation", "ansys", "static", "modal", "buckling", "mesh", "boundary", "contact", "convergence", "finite element", "stress plot", "load case", "element"],
    "cfd": ["cfd", "fluent", "flow", "thermal", "heat", "pressure drop", "reynolds", "turbulence", "y+", "convection", "fluid", "pipe", "velocity", "cooling", "fan", "duct"],
    "manufacturing": ["dfm", "dfa", "manufacturing", "injection", "molding", "moulding", "machining", "sheet metal", "tooling", "cycle time", "scrap", "assembly", "cost", "weld line", "sink", "warpage", "draft", "boss", "rib", "ejector"],
    "materials": ["material", "materials", "ashby", "asm", "steel", "aluminum", "plastic", "abs", "pc", "pp", "nylon", "pa", "peek", "strength", "stiffness", "density", "corrosion", "datasheet", "elastomer"],
    "patent": ["patent", "prior art", "claim", "innovation", "invention", "triz", "novelty", "prototype", "wipo", "uspto", "commercialization"],
}

SEMANTIC_EXPANSIONS = {
    "injection": ["molding", "tooling", "draft", "gate", "ejector", "sink", "warpage", "shrinkage", "ribs", "bosses", "thermoplastic"],
    "cover": ["enclosure", "lid", "housing", "cosmetic", "snap", "boss", "rib", "wall thickness"],
    "shaft": ["torsion", "bending", "fatigue", "keyway", "bearing", "deflection", "critical speed"],
    "beam": ["bending", "deflection", "moment", "support", "load"],
    "fea": ["mesh", "contact", "boundary", "convergence", "validation", "static", "modal", "buckling"],
    "cfd": ["reynolds", "pressure drop", "turbulence", "y plus", "mesh", "boundary", "convergence"],
    "material": ["strength", "stiffness", "toughness", "density", "temperature", "corrosion", "process compatibility", "cost"],
    "solidworks": ["vba", "macro", "api", "feature", "drawing", "bom", "step", "dxf"],
    "patent": ["prior art", "claim", "novelty", "inventive step", "prototype", "triz"],
}

PROTOCOLS = {
    "chief": [
        "Define the decision needed, engineering objective, and acceptance criterion.",
        "Identify function, constraints, loads/physics, material, process, environment, and validation method.",
        "Retrieve internal workspace knowledge and cross-check adjacent domains.",
        "State assumptions, missing data, risk level, confidence, and the next required evidence.",
    ],
    "mechanical": [
        "Define function, loads, supports, geometry, material, life requirement, and environment.",
        "Identify failure modes: yielding, fatigue, deflection, buckling, wear, thermal distortion, looseness, misalignment.",
        "Run hand or sizing calculations before detailed CAD/FEA decisions.",
        "Check manufacturability, tolerance stack-up, assembly, verification, and safety factor.",
    ],
    "manufacturing": [
        "Identify process family, material family, production volume, and cosmetic/functional requirements.",
        "Map geometry to process capability, tooling constraints, cycle time, and defect modes.",
        "Check tolerance feasibility, assembly effort, inspection burden, scrap risk, and repeatability.",
        "Rank design changes by manufacturability impact, quality risk reduction, and cost-down potential.",
    ],
    "materials": [
        "Translate function into material requirements and environmental constraints.",
        "Compare stiffness, strength, toughness, density, thermal limits, corrosion, processing, cost, and availability.",
        "Reject materials that fail environment, process, regulatory, supply, or cost constraints.",
        "Require grade-specific datasheet confirmation before release.",
    ],
    "fea": [
        "Define the simulation question, physics, acceptance criterion, and release decision it supports.",
        "Check load path, constraints, contacts, material model, elements, mesh strategy, and result quantities.",
        "Perform mesh convergence and compare with hand calculation, benchmark, or test data.",
        "Interpret stress plots only after setup verification and singularity screening.",
    ],
    "cfd": [
        "Define flow domain, objective, fluid properties, heat loads, and boundary conditions.",
        "Estimate Reynolds number and select laminar/turbulence model and wall treatment accordingly.",
        "Check mesh quality, y+ target, conservation balances, convergence, and sensitivity.",
        "Validate against analytical pressure drop, heat-transfer estimate, or measured data.",
    ],
    "solidworks": [
        "Clarify document type, units, target geometry, naming convention, and output files.",
        "Separate sketch creation, feature creation, drawings, BOM, export, and error handling.",
        "Protect files from destructive overwrite and define rollback/rebuild checks.",
        "Explain run procedure, validation checks, and limitations of the automation.",
    ],
    "patent": [
        "Separate problem, inventive concept, implementation, and measurable advantage.",
        "Map prior art search keywords, classifications, and closest existing solutions.",
        "Convert concept into testable prototype requirements and claim-like elements.",
        "Avoid legal certainty without patent attorney review.",
    ],
}

ONTOLOGY = {
    "injection molded cover": ["function", "material family", "wall thickness", "draft", "ribs", "bosses", "shrinkage", "sink marks", "warpage", "gate location", "ejector marks", "parting line", "surface class", "snap-fit/screws", "tolerance class", "tooling cost", "cycle time", "validation samples"],
    "shaft": ["torque", "bending moment", "combined stress", "fatigue", "keyway", "bearing seats", "stress concentration", "deflection", "critical speed", "material", "surface finish", "heat treatment"],
    "beam": ["span", "support condition", "load type", "bending stress", "deflection", "section modulus", "moment of inertia", "material", "safety factor"],
    "bracket": ["load path", "constraint realism", "material", "ribbing", "fillets", "bolt pattern", "stress concentration", "manufacturing process", "FEA validation", "safety factor"],
    "pipe flow": ["fluid", "density", "viscosity", "diameter", "velocity", "Reynolds number", "friction factor", "pressure drop", "roughness", "minor losses", "temperature"],
    "sheet metal": ["thickness", "bend radius", "K-factor", "grain direction", "relief", "hole-to-bend distance", "flat pattern", "springback", "tooling"],
    "cad macro": ["document type", "selection manager", "feature manager", "sketch plane", "units", "rebuild", "file overwrite risk", "export path", "error handling"],
}

# =============================================================================
# Knowledge packs: deep organized workspace memory
# =============================================================================
DEEP_KNOWLEDGE_PACKS: Dict[str, Dict[str, str]] = {
    "manufacturing_dfm": {
        "notes.md": """# Manufacturing / DFM Knowledge Pack
Core references:
- Manufacturing process selection methodology
- DFM/DFA logic
- Injection molding, sheet metal, machining, assembly, tolerance, cost, and quality control practice
Engineering rules:
- Match geometry to manufacturing process capability.
- Avoid unnecessary tight tolerances.
- Consider tooling, cycle time, scrap, inspection, assembly, and repeatability.
- Design for production stability, not prototype success only.
""",
        "injection_molding_expert.md": """# Injection Molding Expert DFM Pack
Concept:
Injection molding is a coupled design/manufacturing problem. Geometry, material, tooling, cooling, ejection, surface quality, tolerance capability, and production volume must be considered together.
Rules:
- Confirm material family and grade before final wall thickness, shrinkage, draft, snap-fit behavior, and tolerance decisions.
- Keep nominal wall thickness uniform; avoid thick masses and abrupt transitions.
- Add draft to all pull-direction surfaces; textured surfaces need more draft.
- Use ribs for stiffness instead of thick sections; avoid overly thick rib roots.
- Core bosses and support them with ribs; avoid isolated thick bosses.
- Reserve gate, runner, ejector, parting-line, and shutoff strategy before design freeze.
- Protect cosmetic A-surfaces from gates, ejector pins, sink, weld lines, and parting-line mismatch.
- Avoid tight plastic tolerances unless tied to functional datums and realistic process capability.
Required inputs:
- CAD/STEP or image, material grade, nominal wall thickness, surface class, production volume, assembly method, critical dimensions, tolerance requirements, operating environment.
Failure risks:
- Sink marks, voids, short shot, weld line weakness, warpage, differential shrinkage, flash, ejection damage, brittle snaps, dimensional drift, high cycle time.
""",
        "sheet_metal_expert.md": """# Sheet Metal Expert DFM Pack
Rules:
- Match bend radius, material thickness, tooling, and material ductility.
- Keep holes, slots, embosses, and cutouts away from bend lines.
- Add bend relief where tearing, bulging, or distortion is likely.
- Minimize bend setups and complex forming directions.
- Define grain direction, flat pattern, K-factor, finish side, and burr direction.
- Avoid tight flatness/perpendicularity without process capability evidence.
Required inputs:
- Material, thickness, bend radius, bend count, hole positions, tolerance class, surface finish, annual volume.
Failure risks:
- Cracking, springback, hole distortion, burrs, flatness loss, tolerance stack-up, cosmetic handling damage.
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
- Avoid hidden fasteners, inaccessible clips, ambiguous orientation, and fragile assembly features.
- Design datums, stops, lead-ins, and inspection features into the product.
Required inputs:
- Assembly method, mating parts, access direction, serviceability requirements, operator/tool constraints, takt time.
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
Cost-down levers:
- Part consolidation, wall-thickness optimization, ribbing instead of mass, simplified tooling, standard fasteners, datum simplification, reduced inspection, common material grades, and fewer finishing operations.
""",
        "quality_control_expert.md": """# Manufacturing Quality Control Expert Pack
Rules:
- Define CTQs: critical-to-quality dimensions, cosmetic zones, functional interfaces, and safety-related checks.
- Link inspection method to tolerance and production volume.
- Separate incoming material checks, in-process checks, final inspection, and validation tests.
- Use control plans for high-volume production.
Defect modes:
- Sink, flash, warpage, short shot, weld-line weakness, burrs, dimensional drift, assembly force, cosmetic damage.
Validation:
- Use first article inspection, capability checks, functional tests, environmental exposure, and pilot build feedback before release.
""",
    },
    "mechanical_design": {
        "notes.md": """# Mechanical Design Knowledge Pack
Core references:
- Shigley-style mechanical design methodology
- Roark-style stress/deflection formulas
- Machinery Handbook practice
- GD&T and design verification logic
Engineering rules:
- Define loads, constraints, materials, environment, safety factor, and validation method.
- Check manufacturability, tolerance stack-up, failure modes, and test plan before final design.
- Use hand calculations as sanity checks before simulation.
""",
        "shafts.md": """# Shaft Design Expert Pack
Rules:
- Evaluate torque, bending, axial loads, keyways, shoulders, bearing seats, and stress concentrations.
- Check static yield, fatigue, deflection, critical speed, and bearing interface requirements.
- Avoid abrupt diameter changes; use fillets and reliefs.
- Define surface finish and heat treatment where fatigue or wear matters.
Required inputs:
- Torque, bending moment, span, bearing layout, material, keyway geometry, duty cycle, speed, safety factor.
Calculations:
- Torsional shear stress, bending stress, combined stress, deflection, fatigue safety factor, critical speed.
""",
        "beams.md": """# Beam Design Expert Pack
Rules:
- Define support condition, load type, span, material, section properties, allowable stress, and deflection limit.
- Check bending stress, shear stress, deflection, local stress concentration, and stability.
- Compare hand calculations with FEA for brackets, frames, and beams.
Required inputs:
- Load magnitude, load location, span, support type, E, yield strength, cross-section, allowable deflection.
""",
        "bearings.md": """# Bearing Selection Expert Pack
Rules:
- Define radial load, axial load, speed, life target, environment, lubrication, mounting, and misalignment.
- Check dynamic capacity, static capacity, equivalent load, L10 life, shaft/housing fits, preload/clearance, sealing.
Required inputs:
- Load components, RPM, life hours, bearing type, lubrication, temperature, contamination, fit class.
""",
        "gears.md": """# Gear Design Expert Pack
Rules:
- Define ratio, torque, speed, module/diametral pitch, face width, material, heat treatment, accuracy, lubrication, noise limits.
- Check bending strength, contact stress, wear, backlash, center distance, and manufacturing process.
Required inputs:
- Power, speed, ratio, gear type, material, duty cycle, service factor, size constraints.
""",
        "springs.md": """# Spring Design Expert Pack
Rules:
- Define load-deflection requirement, solid height, working range, fatigue life, material, environment, end conditions.
- Check shear stress, spring rate, buckling, surge, fatigue, and manufacturability.
Required inputs:
- Force range, deflection range, space envelope, cycle count, temperature, corrosion exposure.
""",
        "fasteners.md": """# Fastener Design Expert Pack
Rules:
- Define joint function, preload, service loads, material stack, thread engagement, locking method, access, and serviceability.
- Check clamp load, shear, bearing, pull-out, fatigue, loosening, corrosion, and torque scatter.
Required inputs:
- Bolt size, grade, preload target, joint material, load direction, friction assumptions, environment.
""",
        "fatigue.md": """# Fatigue Design Expert Pack
Rules:
- Identify cyclic loads, mean stress, stress concentration, surface finish, size effect, temperature, corrosion, and reliability target.
- Avoid sharp notches; improve radii and surface finish.
- Validate fatigue-critical parts with test data or conservative design factors.
Required inputs:
- Stress amplitude, mean stress, cycle count, material S-N data, notch factor, surface finish, reliability.
""",
        "gdnt_tolerances.md": """# GD&T and Tolerance Reasoning Pack
Rules:
- Use datums that reflect function, assembly, manufacturing, and inspection.
- Tighten tolerances only where function requires it.
- Separate size tolerance, form, orientation, location, and runout requirements.
- Perform tolerance stack-up for mating assemblies.
Required inputs:
- Functional interfaces, datum scheme, manufacturing process, inspection method, critical dimensions.
""",
    },
    "simulation_fea": {
        "notes.md": """# Simulation / FEA Knowledge Pack
Rules:
- Define objective and acceptance criteria before model setup.
- Validate load path, constraints, contacts, mesh, material model, and convergence.
- Compare with hand calculations, benchmarks, or test data.
""",
        "static_structural.md": """# Static Structural FEA Expert Pack
Rules:
- Define load cases, constraints, contacts, material model, units, and acceptance criteria.
- Use realistic constraints that preserve actual load paths.
- Check reaction forces, stress concentrations, singularities, deformation shape, and mesh sensitivity.
Required inputs:
- CAD, material, loads, boundary conditions, contacts, expected failure criterion, allowable stress/deflection.
""",
        "modal_analysis.md": """# Modal Analysis Expert Pack
Rules:
- Define boundary condition realism, mass participation, frequency range, and operational excitation sources.
- Verify constraints, contacts, mass properties, and mesh before interpreting modes.
Required inputs:
- Assembly constraints, mass distribution, stiffness interfaces, excitation frequencies, operating speed.
""",
        "buckling.md": """# Buckling FEA Expert Pack
Rules:
- Treat linear buckling as a screening tool, not final evidence.
- Include imperfections, nonlinear geometry/material behavior, and realistic boundary conditions for release decisions.
Required inputs:
- Geometry slenderness, load path, constraints, material, imperfection assumptions, safety factor.
""",
        "fatigue_fea.md": """# FEA Fatigue Expert Pack
Rules:
- Fatigue requires stress history, mean stress correction, material S-N data, notch treatment, surface finish, and reliability.
- Avoid using raw peak singular stress for fatigue decisions.
Required inputs:
- Cyclic load history, material fatigue data, surface finish, notch factors, target life.
""",
        "contacts.md": """# FEA Contact Expert Pack
Rules:
- Contact assumptions can dominate stiffness and stress results.
- Check bonded/no-separation/frictional contact definitions and penetration tolerances.
- Validate contact pressure, separation, sliding, and convergence.
Required inputs:
- Interface function, friction, preload, contact area, assembly sequence.
""",
        "mesh_convergence.md": """# Mesh Convergence Expert Pack
Rules:
- Refine around holes, fillets, contacts, load introduction, and stress gradients.
- Track displacement, reaction, and stress away from singularities.
- Do not trust a single mesh result.
Required inputs:
- Mesh sizes, element type, convergence target, result quantity to monitor.
""",
        "validation.md": """# FEA Validation Expert Pack
Rules:
- Every simulation supporting release needs validation logic.
- Compare with hand calculation, test, benchmark, or known behavior.
- Report assumptions, limitations, and confidence.
Required inputs:
- Acceptance criteria, validation method, test data or analytical baseline.
""",
    },
    "cfd_thermal": {
        "notes.md": """# CFD / Thermal Knowledge Pack
Rules:
- Identify flow regime, boundary conditions, mesh quality, y+, convergence, and conservation balances.
- Validate CFD with analytical estimates or experiments.
""",
        "internal_flow.md": """# Internal Flow Expert Pack
Rules:
- Compute Reynolds number before selecting laminar/turbulent model.
- Check entrance length, roughness, minor losses, pressure drop, and mass balance.
Required inputs:
- Fluid, density, viscosity, diameter, length, roughness, flow rate/velocity, temperature.
""",
        "external_flow.md": """# External Flow Expert Pack
Rules:
- Define far-field domain, blockage ratio, boundary conditions, turbulence intensity, and wake resolution.
- Validate drag/heat transfer with estimates or experiments.
Required inputs:
- Geometry, velocity, fluid properties, domain size, wall/thermal conditions.
""",
        "reynolds_number.md": """# Reynolds Number Reasoning Pack
Rules:
- Re = rho * V * D / mu.
- Low Re suggests laminar behavior; high Re suggests turbulence, but geometry and disturbances matter.
- Use hydraulic diameter for non-circular ducts.
Required inputs:
- Density, velocity, characteristic length/diameter, dynamic viscosity.
""",
        "turbulence_models.md": """# Turbulence Model Expert Pack
Rules:
- k-epsilon is robust for many industrial internal flows but weak near walls/separation.
- k-omega SST is often better for adverse pressure gradients and separation.
- Wall treatment and y+ target must match model choice.
Required inputs:
- Flow type, separation risk, wall heat transfer importance, mesh resolution, y+ target.
""",
        "y_plus.md": """# y+ Wall Treatment Pack
Rules:
- y+ strategy must match turbulence model and wall function/resolved wall approach.
- Heat transfer and wall shear predictions are sensitive to near-wall mesh.
Required inputs:
- Fluid properties, velocity scale, wall shear estimate, first cell height, turbulence model.
""",
        "pressure_drop.md": """# Pressure Drop Expert Pack
Rules:
- Estimate pressure drop analytically before CFD.
- Include major losses, minor losses, fittings, entrance/exit, roughness, and regime.
Required inputs:
- Flow rate, diameter, length, roughness, fittings, density, viscosity.
""",
        "heat_transfer.md": """# Heat Transfer Expert Pack
Rules:
- Separate conduction, convection, radiation, and contact resistance.
- Use thermal resistance networks as sanity checks before CFD.
- Validate temperatures against heat load and boundary conditions.
Required inputs:
- Heat load, geometry, material conductivity, fluid conditions, convection coefficient, ambient temperature.
""",
    },
    "materials_selection": {
        "notes.md": """# Materials Selection Knowledge Pack
Rules:
- Start from functional requirements, not material preference.
- Compare stiffness, strength, toughness, density, thermal limits, corrosion, process compatibility, cost, and availability.
- Verify grade-specific datasheets before release.
""",
        "thermoplastics.md": """# Thermoplastics Expert Pack
Rules:
- ABS: useful for covers and cosmetics; verify heat and chemical exposure.
- PP: low density and chemical resistance; lower stiffness and higher shrinkage risk.
- PC: high impact; check stress cracking and processing.
- PA/Nylon: toughness and wear; moisture affects dimensions.
- PEEK: high performance and temperature; high cost and processing considerations.
Required inputs:
- Temperature, chemical exposure, impact, stiffness, surface finish, process, cost, availability.
""",
        "metals.md": """# Metals Selection Expert Pack
Rules:
- Steel: strength and stiffness; corrosion protection may be needed.
- Stainless: corrosion resistance; cost and machinability vary by grade.
- Aluminum: low density and corrosion resistance; lower modulus and fatigue considerations.
- Brass/copper: conductivity and machinability; cost and galvanic corrosion must be checked.
Required inputs:
- Strength, stiffness, corrosion, weight target, manufacturing process, fatigue, cost.
""",
        "elastomers.md": """# Elastomers Expert Pack
Rules:
- Select by hardness, compression set, temperature, chemical exposure, fatigue, sealing force, and manufacturing method.
- Check creep, aging, UV, ozone, and fluid compatibility.
Required inputs:
- Shore hardness, compression, fluid, temperature, life, sealing geometry.
""",
        "corrosion.md": """# Corrosion Material Reasoning Pack
Rules:
- Identify environment: water, salt, chemicals, temperature, galvanic couples, humidity, UV.
- Avoid galvanic pairs without isolation or coatings.
- Validate coating, passivation, or material upgrade using exposure requirements.
Required inputs:
- Environment, mating materials, coating, life target, maintenance, regulatory constraints.
""",
        "temperature_limits.md": """# Temperature Limits Pack
Rules:
- Check continuous-use temperature, heat deflection, glass transition, creep, oxidation, and thermal cycling.
- For plastics, temperature can reduce stiffness and increase creep.
Required inputs:
- Peak temperature, continuous temperature, load at temperature, duration, thermal cycling.
""",
        "ashby_selection_logic.md": """# Ashby-Style Selection Logic Pack
Rules:
- Define function, objective, constraints, and free variables.
- Screen materials by hard constraints, then rank by performance index and cost/supply.
- Validate candidate materials using grade datasheets and manufacturing compatibility.
Required inputs:
- Function, constraints, objective, process, environment, cost target, availability.
""",
    },
    "cad_solidworks": {
        "notes.md": """# CAD / SolidWorks Knowledge Pack
Rules:
- Prefer parametric, editable CAD with clear units, dimensions, feature names, and verification steps.
- Separate modeling, drawings, BOM, export, and automation error handling.
""",
        "macro_architecture.md": """# SolidWorks Macro Architecture Pack
Rules:
- Separate input validation, document creation, sketch creation, feature creation, rebuild, export, and error handling.
- Always define units and document type.
- Avoid destructive operations without confirmation.
Required inputs:
- Part/assembly/drawing target, units, dimensions, output folder, overwrite policy.
""",
        "vba_api.md": """# SolidWorks VBA/API Pack
Rules:
- Use clear object references: SldWorks, ModelDoc2, FeatureManager, SketchManager, SelectionMgr.
- Check return values after feature creation and save/export calls.
- Rebuild and validate geometry after automation.
""",
        "drawing_bom.md": """# Drawing and BOM Automation Pack
Rules:
- Define drawing template, sheet size, view orientation, scale, dimensions, tolerances, title block, and BOM columns.
- Verify references and missing custom properties before release.
""",
        "step_dxf_export.md": """# STEP/DXF Export Pack
Rules:
- Define target version, units, file naming, output folder, flat pattern state, and revision.
- Check export success and file existence.
- For sheet metal DXF, confirm correct flat pattern and bend lines.
""",
        "modeling_strategy.md": """# CAD Modeling Strategy Pack
Rules:
- Build robust parametric features with stable references.
- Avoid over-constraining sketches or referencing fragile edges.
- Name important dimensions and features for automation.
""",
        "automation_safety.md": """# CAD Automation Safety Pack
Rules:
- Warn before overwrite, mass delete, rebuild all, or batch export.
- Log actions and create backups when modifying many files.
- Validate results after automation.
""",
    },
    "innovation_patent": {
        "notes.md": """# Innovation / Patent Knowledge Pack
Rules:
- Separate novelty, usefulness, manufacturability, and commercial value.
- Search prior art before heavy development investment.
- Convert ideas into testable prototype requirements.
""",
        "triz.md": """# TRIZ Reasoning Pack
Rules:
- Identify contradiction: improving one parameter worsens another.
- Search for separation principles, inventive principles, and alternative physical effects.
Required inputs:
- Problem statement, constraints, current solution, failure mode, target improvement.
""",
        "prior_art.md": """# Prior-Art Search Pack
Rules:
- Search by problem, function, mechanism, industry, synonyms, patent classifications, and competitor products.
- Record closest references and differentiating features.
""",
        "novelty_readiness.md": """# Novelty Readiness Pack
Rules:
- A concept is not ready for patent drafting until the inventive feature, advantage, implementation, and closest prior art are clear.
- Avoid legal certainty without attorney review.
""",
        "prototype_validation.md": """# Prototype Validation Pack
Rules:
- Convert the invention into measurable claims and prototype tests.
- Define pass/fail criteria, manufacturing route, risk, and cost.
""",
        "claims_logic.md": """# Patent Claim Logic Pack
Rules:
- Identify independent concept, dependent refinements, alternatives, and embodiments.
- Avoid overly narrow features unless they are essential.
""",
        "commercialization.md": """# Commercialization Reasoning Pack
Rules:
- Evaluate market pain, manufacturability, cost, regulatory issues, distribution, IP position, and prototype evidence.
""",
    },
}

# =============================================================================
# Data classes
# =============================================================================
@dataclass
class DocumentChunk:
    pack: str
    title: str
    path: str
    topic: str
    section: str
    text: str
    score_quality: float
    tokens: set = field(default_factory=set)

@dataclass
class RetrievalHit:
    pack: str
    title: str
    path: str
    topic: str
    section: str
    score: float
    confidence: str
    text: str

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
    intent_notes: List[str]

@dataclass
class RiskItem:
    area: str
    risk: str
    reason: str
    required_data: str
    action: str

@dataclass
class ScoreCard:
    name: str
    score: int
    level: str
    items: List[RiskItem]
    recommendations: List[str]

# =============================================================================
# Knowledge pack seeding / loading
# =============================================================================
def seed_knowledge_packs() -> None:
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    for pack, files in DEEP_KNOWLEDGE_PACKS.items():
        folder = KNOWLEDGE_DIR / pack
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "source_docs").mkdir(exist_ok=True)
        for filename, content in files.items():
            target = folder / filename
            if not target.exists() or target.read_text(encoding="utf-8", errors="ignore").strip()[:20] == "":
                target.write_text(content.strip() + "\n", encoding="utf-8")

def relative_path(p: Path) -> str:
    try:
        return str(p.relative_to(APP_DIR)).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")

def clean_text(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"[#*_`>\"|]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9\+\#\.\-/]+|[\u0600-\u06FF]+", text.lower())

def expand_query(query: str) -> str:
    words = tokenize(query)
    expanded = list(words)
    q = query.lower()
    for key, additions in SEMANTIC_EXPANSIONS.items():
        if key in q:
            expanded.extend(tokenize(" ".join(additions)))
    return " ".join(expanded)

def split_markdown_sections(text: str) -> List[Tuple[str, str]]:
    sections: List[Tuple[str, str]] = []
    current_title = "general"
    current_lines: List[str] = []
    for line in text.splitlines():
        if line.strip().startswith("#"):
            if current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = re.sub(r"^#+\s*", "", line.strip()) or "section"
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))
    return [(t, c) for t, c in sections if c.strip()]

def topic_from_filename(path: Path) -> str:
    return path.stem.replace("_", " ").replace("expert", "").strip().title()

def source_quality(path: Path, text: str) -> float:
    name = path.name.lower()
    score = 1.0
    if "expert" in name: score += 0.6
    if "protocol" in text.lower(): score += 0.15
    if "required inputs" in text.lower(): score += 0.15
    if "decision logic" in text.lower(): score += 0.2
    if "rules" in text.lower(): score += 0.1
    return round(score, 2)

@st.cache_data(show_spinner=False)
def load_chunks() -> List[DocumentChunk]:
    seed_knowledge_packs()
    chunks: List[DocumentChunk] = []
    for md in sorted(KNOWLEDGE_DIR.glob("**/*.md")):
        if "source_docs" in md.parts:
            continue
        pack = md.relative_to(KNOWLEDGE_DIR).parts[0]
        title = PACK_TITLES.get(pack, pack.replace("_", " ").title())
        raw = md.read_text(encoding="utf-8", errors="ignore")
        sections = split_markdown_sections(raw)
        if not sections:
            sections = [(topic_from_filename(md), raw)]
        for section, body in sections:
            content = clean_text(f"{topic_from_filename(md)} {section} {body}")
            if not content:
                continue
            chunks.append(DocumentChunk(
                pack=pack,
                title=title,
                path=relative_path(md),
                topic=topic_from_filename(md),
                section=section,
                text=content,
                score_quality=source_quality(md, raw),
                tokens=set(tokenize(content)),
            ))
    return chunks

# =============================================================================
# Routing + retrieval
# =============================================================================
def infer_agent(query: str) -> str:
    q = query.lower()
    best_agent = "chief"
    best_score = 0
    for agent, words in INTENT_KEYWORDS.items():
        score = 0
        for w in words:
            if w in q:
                score += 5 if " " in w else 2
        if score > best_score:
            best_score = score
            best_agent = agent
    return best_agent

def route_agent(query: str, selected_workspace: str) -> str:
    inferred = infer_agent(query)
    if inferred != "chief":
        return inferred
    return selected_workspace or "chief"

def phrase_boost(query: str, chunk: DocumentChunk, preferred_pack: str, inferred_pack: str) -> float:
    q = query.lower()
    filename = Path(chunk.path).name.lower()
    pack = chunk.pack
    score = 0.0
    if preferred_pack and pack == preferred_pack: score += 5.0
    if inferred_pack and pack == inferred_pack: score += 9.0
    boosts = [
        (["injection", "mold", "mould", "draft", "sink", "warpage", "boss", "rib"], "manufacturing_dfm", 16, "injection"),
        (["sheet metal", "bend", "flat pattern"], "manufacturing_dfm", 12, "sheet"),
        (["machining", "milling", "turning", "tool"], "manufacturing_dfm", 10, "machining"),
        (["assembly", "dfa", "fastener"], "manufacturing_dfm", 8, "assembly"),
        (["abs", "pp", "pc", "nylon", "thermoplastic", "plastic"], "materials_selection", 12, "thermoplastic"),
        (["shaft", "torsion", "keyway"], "mechanical_design", 12, "shaft"),
        (["beam", "deflection", "bending"], "mechanical_design", 10, "beam"),
        (["bearing", "l10"], "mechanical_design", 10, "bearing"),
        (["fea", "mesh", "static", "contact", "modal", "buckling"], "simulation_fea", 12, ""),
        (["cfd", "reynolds", "pressure drop", "turbulence", "y+", "heat transfer"], "cfd_thermal", 12, ""),
        (["solidworks", "macro", "vba", "dxf", "step"], "cad_solidworks", 12, ""),
        (["patent", "prior art", "claim", "triz"], "innovation_patent", 12, ""),
    ]
    for words, target_pack, value, filename_hint in boosts:
        if any(w in q for w in words) and pack == target_pack:
            score += value
            if filename_hint and filename_hint in filename:
                score += value * 0.7
    return score

def retrieve_knowledge(query: str, agent: str, top_k: int = 7) -> List[RetrievalHit]:
    chunks = load_chunks()
    expanded_query = expand_query(query)
    q_tokens = set(tokenize(expanded_query))
    preferred_pack = WORKSPACE_TO_PACK.get(agent, "")
    inferred_pack = WORKSPACE_TO_PACK.get(infer_agent(query), "")
    hits: List[RetrievalHit] = []
    for ch in chunks:
        overlap = len(q_tokens & ch.tokens)
        if overlap == 0:
            base = 0.0
        else:
            base = overlap * 1.25
        score = base + phrase_boost(query, ch, preferred_pack, inferred_pack) + ch.score_quality
        if score <= 1.1:
            continue
        confidence = "High" if score >= 18 else "Medium" if score >= 9 else "Low"
        hits.append(RetrievalHit(ch.pack, ch.title, ch.path, ch.topic, ch.section, round(score, 3), confidence, ch.text[:650]))
    hits.sort(key=lambda h: h.score, reverse=True)
    # diversify by file, but keep top relevant
    selected: List[RetrievalHit] = []
    seen_paths: set = set()
    for h in hits:
        if h.path not in seen_paths or len(selected) < 3:
            selected.append(h)
            seen_paths.add(h.path)
        if len(selected) >= top_k:
            break
    return selected

# =============================================================================
# Query framing
# =============================================================================
def infer_part_type(q: str) -> str:
    s = q.lower()
    if "cover" in s or "lid" in s: return "cover/enclosure"
    if "shaft" in s: return "shaft"
    if "bracket" in s: return "bracket"
    if "pipe" in s or "duct" in s: return "pipe/duct"
    if "gear" in s: return "gear"
    if "spring" in s: return "spring"
    if "housing" in s: return "housing"
    return "unspecified component"

def infer_process(q: str, agent: str) -> str:
    s = q.lower()
    if "injection" in s or "mold" in s or "mould" in s: return "injection molding"
    if "sheet metal" in s or "bend" in s: return "sheet metal fabrication"
    if "machining" in s or "milling" in s or "turning" in s: return "machining"
    if "casting" in s: return "casting"
    if agent == "manufacturing": return "manufacturing process not fully specified"
    if agent == "cfd": return "fluid/thermal physics"
    if agent == "fea": return "structural simulation"
    return "not specified"

def extract_materials(q: str) -> List[str]:
    candidates = ["abs", "pp", "pc", "pa", "nylon", "peek", "aluminum", "aluminium", "steel", "stainless", "brass", "copper", "polycarbonate", "polypropylene", "rubber", "silicone"]
    s = q.lower()
    vals = []
    for c in candidates:
        if re.search(rf"\b{re.escape(c)}\b", s):
            vals.append(c.upper() if c in ["abs", "pp", "pc", "pa", "peek"] else c.title())
    return sorted(set(vals))

def extract_quantities(q: str) -> List[str]:
    pattern = r"\b\d+(?:\.\d+)?\s*(?:mm|cm|m|n|kn|nm|n\*m|mpa|gpa|bar|pa|kg|g|rpm|c|°c|w|kw|l/min|m/s|units/year|pcs|pieces|%)\b"
    return re.findall(pattern, q.lower())

def related_concepts(query: str) -> List[str]:
    q = query.lower()
    concepts: List[str] = []
    for key, values in ONTOLOGY.items():
        if key in q or any(w in q for w in key.split()):
            concepts.extend(values)
    if "dfm" in q or "injection" in q or "mold" in q:
        concepts.extend(ONTOLOGY["injection molded cover"])
    return list(dict.fromkeys(concepts))[:18]

def missing_data_for(agent: str, process: str, part: str, materials: List[str], quantities: List[str]) -> List[str]:
    missing: List[str] = []
    if part == "unspecified component": missing.append("component function and part type")
    if not materials: missing.append("material family and grade")
    if not quantities: missing.append("key dimensions, loads, tolerances, or operating values")
    if agent == "manufacturing" or process == "injection molding":
        missing += ["CAD/STEP or image", "nominal wall thickness", "production volume", "surface/cosmetic class", "assembly method", "critical dimensions/tolerances", "gate/ejector/parting-line constraints"]
    if agent == "mechanical":
        missing += ["load case", "material properties", "geometry/section properties", "allowable stress/deflection", "life requirement"]
    if agent == "fea":
        missing += ["load cases", "constraints", "contacts", "material model", "acceptance criterion", "mesh convergence target"]
    if agent == "cfd":
        missing += ["fluid properties", "flow rate or velocity", "domain geometry", "boundary conditions", "temperature/heat load", "mesh/y+ target"]
    if agent == "materials":
        missing += ["temperature range", "chemical exposure", "stiffness/strength target", "manufacturing process", "cost target", "availability constraints"]
    if agent == "solidworks":
        missing += ["document type", "units", "dimensions", "output path", "overwrite policy"]
    if agent == "patent":
        missing += ["closest prior art", "inventive feature", "technical advantage", "prototype evidence"]
    return list(dict.fromkeys(missing))[:12]

def confidence_level(missing: List[str], hits: List[RetrievalHit]) -> str:
    source_bonus = sum(1 for h in hits if h.confidence in ["High", "Medium"])
    if len(missing) >= 7 or source_bonus <= 1: return "Low-to-medium"
    if len(missing) >= 4: return "Medium"
    return "Medium-to-high"

def build_query_frame(query: str, agent: str, hits: List[RetrievalHit]) -> QueryFrame:
    part = infer_part_type(query)
    process = infer_process(query, agent)
    materials = extract_materials(query)
    quantities = extract_quantities(query)
    concepts = related_concepts(query)
    missing = missing_data_for(agent, process, part, materials, quantities)
    notes = []
    if agent == "manufacturing" and process == "injection molding": notes.append("DFM path selected because injection molding terms were detected.")
    if not materials: notes.append("Material-dependent limits cannot be finalized without grade-specific data.")
    return QueryFrame(agent, part, process, materials, quantities, concepts, missing, confidence_level(missing, hits), notes)

# =============================================================================
# Scoring engines and decision logic
# =============================================================================
RISK_VALUE = {"Low": 5, "Medium": 12, "High": 20, "Unknown": 14}

def has_any(q: str, words: Iterable[str]) -> bool:
    s = q.lower()
    return any(w in s for w in words)

def score_from_risks(items: List[RiskItem], missing_count: int = 0) -> int:
    penalty = sum(RISK_VALUE.get(i.risk, 10) for i in items) + min(missing_count, 10) * 2
    return max(5, min(100, 100 - penalty))

def level_from_score(score: int) -> str:
    if score >= 80: return "Good / controlled"
    if score >= 60: return "Moderate risk"
    if score >= 40: return "Medium-high risk"
    return "High risk / insufficient data"

def dfm_scorecard(query: str, frame: QueryFrame) -> ScoreCard:
    q = query.lower()
    items = [
        RiskItem("Wall thickness", "High" if "wall" not in q and not re.search(r"\d+(?:\.\d+)?\s*mm", q) else "Medium", "Injection molded parts are sensitive to non-uniform wall thickness, sink, and warpage.", "Nominal wall thickness map and material grade.", "Keep thickness uniform, avoid abrupt masses, and validate sink/warpage."),
        RiskItem("Draft", "Medium" if "draft" not in q else "Low", "Mold release requires draft on pull-direction faces, ribs, bosses, and texture.", "Draft angles, texture class, pull direction.", "Add process-appropriate draft early and confirm with tooling."),
        RiskItem("Ribs / bosses", "High" if "rib" not in q and "boss" not in q else "Medium", "Covers often need stiffness and mounting features; poor bosses/ribs create sink and weak joints.", "Rib height/thickness, boss diameter, screw/snap strategy.", "Use ribs for stiffness, core bosses, and avoid isolated thick sections."),
        RiskItem("Tooling strategy", "Medium", "Gate, ejector, parting line, shutoffs, and cooling can drive cosmetic and dimensional defects.", "Gate/ejector/parting-line constraints and surface class.", "Reserve tooling strategy before design freeze."),
        RiskItem("Tolerance capability", "Unknown", "Plastic shrinkage, cavity variation, moisture, and temperature affect dimensions.", "Critical dimensions and tolerance class.", "Tie tight tolerances to functional datums and inspection methods."),
        RiskItem("Assembly / DFA", "Unknown", "Assembly method controls snap fits, screws, inserts, bosses, access, and tolerance stack-up.", "Mating parts and assembly method.", "Define assembly method before freezing bosses, clips, inserts, and datums."),
    ]
    score = score_from_risks(items, len(frame.missing_data))
    recommendations = [
        "Request CAD/STEP or at least annotated images before release-level DFM.",
        "Confirm material family/grade and nominal wall thickness before setting tooling assumptions.",
        "Prioritize wall uniformity, draft, boss/rib strategy, and cosmetic surface protection.",
        "Create a CTQ list covering functional interfaces, cosmetic zones, and inspection method.",
    ]
    return ScoreCard("DFM Score", score, level_from_score(score), items, recommendations)

def dfa_scorecard(query: str, frame: QueryFrame) -> ScoreCard:
    items = [
        RiskItem("Part count", "Unknown", "Part count and fastener count are not provided.", "Assembly BOM and fastening strategy.", "Reduce part/fastener count where function allows."),
        RiskItem("Assembly access", "Unknown", "Tool access and insertion direction are undefined.", "Assembly direction, tool clearance, mating parts.", "Use self-locating features and visible access paths."),
        RiskItem("Mistake proofing", "Medium", "Orientation and operator error risk are unknown.", "Symmetry, poka-yoke features, operator sequence.", "Add asymmetric locating features where needed."),
    ]
    score = score_from_risks(items, len(frame.missing_data)//2)
    return ScoreCard("DFA Score", score, level_from_score(score), items, ["Define assembly sequence and mating parts.", "Use self-locating features and reduce fastener operations."])

def fea_scorecard(query: str, frame: QueryFrame) -> ScoreCard:
    items = [
        RiskItem("Objective", "High" if "stress" not in query.lower() and "deflection" not in query.lower() else "Medium", "Simulation objective/acceptance criterion is not explicit.", "Acceptance criterion and result quantity.", "State what decision the FEA supports."),
        RiskItem("Boundary conditions", "High", "Constraints and load path are not defined.", "Loads, supports, contacts, preload.", "Model realistic constraints and check reaction forces."),
        RiskItem("Mesh convergence", "High", "No convergence target or mesh strategy is provided.", "Element type, mesh sizes, monitored outputs.", "Run mesh convergence away from singularities."),
        RiskItem("Validation", "High", "No hand calculation, benchmark, or test validation is stated.", "Validation method.", "Compare results to hand calculations or tests."),
    ]
    score = score_from_risks(items, len(frame.missing_data))
    return ScoreCard("FEA Setup Quality Score", score, level_from_score(score), items, ["Define objective, constraints, contacts, mesh convergence, and validation before solving."])

def cfd_scorecard(query: str, frame: QueryFrame) -> ScoreCard:
    items = [
        RiskItem("Flow regime", "High" if not has_any(query, ["reynolds", "velocity", "flow rate", "diameter"]) else "Medium", "Flow regime cannot be classified without properties and velocity/flow rate.", "Fluid properties, velocity/flow rate, characteristic length.", "Compute Reynolds number before model selection."),
        RiskItem("Boundary conditions", "High", "Inlet/outlet/thermal boundaries are not defined.", "Boundary conditions and heat loads.", "Define physical boundaries and check conservation balances."),
        RiskItem("Mesh/y+", "High", "Near-wall resolution strategy is not defined.", "Turbulence model and y+ target.", "Set mesh/y+ strategy to match model and wall heat/shear needs."),
        RiskItem("Validation", "High", "No analytical or test validation is stated.", "Pressure-drop or heat-transfer baseline.", "Validate CFD with simplified calculations or measurements."),
    ]
    score = score_from_risks(items, len(frame.missing_data))
    return ScoreCard("CFD Setup Quality Score", score, level_from_score(score), items, ["Calculate Reynolds number and pressure-drop/heat-transfer baseline before CFD."])

def material_scorecard(query: str, frame: QueryFrame) -> ScoreCard:
    items = [
        RiskItem("Functional requirements", "High", "Material objective is not fully defined.", "Strength, stiffness, toughness, density, temperature, cost targets.", "Define hard constraints before selecting materials."),
        RiskItem("Environment", "High", "Temperature, chemicals, UV, moisture, and corrosion exposure are unknown.", "Operating environment.", "Screen candidates against environmental limits."),
        RiskItem("Process compatibility", "Medium", "Manufacturing process/material interaction must be checked.", "Process and supplier grade.", "Validate process compatibility with grade datasheet."),
        RiskItem("Availability/cost", "Medium", "Supply and cost constraints are not specified.", "Cost target, availability, suppliers.", "Rank candidates by performance and supply risk."),
    ]
    score = score_from_risks(items, len(frame.missing_data))
    return ScoreCard("Material Suitability Score", score, level_from_score(score), items, ["Use Ashby-style screening: constraints first, ranking second, datasheet validation last."])

def cad_scorecard(query: str, frame: QueryFrame) -> ScoreCard:
    items = [
        RiskItem("Document context", "High", "Part/assembly/drawing context is not fully defined.", "Document type, units, target geometry.", "Clarify CAD document and units before automation."),
        RiskItem("Destructive operations", "Medium", "Overwrite and batch-operation risks are unknown.", "Output paths and overwrite policy.", "Add safety checks and backups."),
        RiskItem("Verification", "Medium", "Rebuild/export validation is not defined.", "Validation method.", "Check rebuild, file existence, and exported geometry."),
    ]
    score = max(0, 100 - sum(RISK_VALUE[i.risk] for i in items))
    return ScoreCard("CAD Automation Risk Score", score, level_from_score(score), items, ["Separate macro into input validation, geometry, drawing/BOM, export, and verification."])

def patent_scorecard(query: str, frame: QueryFrame) -> ScoreCard:
    items = [
        RiskItem("Prior art", "High", "No closest prior art is identified.", "Search keywords, classifications, competitor products.", "Run prior-art search before patent investment."),
        RiskItem("Inventive feature", "High", "The differentiating technical feature is not defined.", "Problem, mechanism, advantage.", "State the novel mechanism and measurable benefit."),
        RiskItem("Prototype evidence", "Medium", "No validation evidence is provided.", "Prototype tests and pass/fail criteria.", "Convert concept into testable prototype requirements."),
    ]
    score = score_from_risks(items, len(frame.missing_data)//2)
    return ScoreCard("Patent Novelty Readiness Score", score, level_from_score(score), items, ["Clarify invention, closest prior art, technical advantage, and prototype evidence."])

def build_scorecards(query: str, agent: str, frame: QueryFrame) -> List[ScoreCard]:
    if agent == "manufacturing": return [dfm_scorecard(query, frame), dfa_scorecard(query, frame)]
    if agent == "fea": return [fea_scorecard(query, frame)]
    if agent == "cfd": return [cfd_scorecard(query, frame)]
    if agent == "materials": return [material_scorecard(query, frame)]
    if agent == "solidworks": return [cad_scorecard(query, frame)]
    if agent == "patent": return [patent_scorecard(query, frame)]
    if agent == "mechanical": return [ScoreCard("Mechanical Design Readiness Score", 55, "Moderate risk", [
        RiskItem("Loads", "High", "Loads/supports are not fully specified.", "Load cases and constraints.", "Define loads and allowable limits."),
        RiskItem("Material", "Medium", "Material properties may be missing.", "Material and properties.", "Confirm material grade and safety factor."),
        RiskItem("Validation", "High", "No verification method is defined.", "Hand calc, test, or simulation plan.", "Run sanity calculations and validation."),
    ], ["Define loads, geometry, material, failure mode, safety factor, and validation method."])]
    return [dfm_scorecard(query, frame)] if "dfm" in query.lower() or "manufact" in query.lower() else []

# =============================================================================
# Engineering calculators / validators
# =============================================================================
def extract_value(query: str, labels: List[str], unit_patterns: List[str]) -> Optional[float]:
    q = query.lower()
    for label in labels:
        for unit in unit_patterns:
            m = re.search(rf"{label}\s*[=:]?\s*(\d+(?:\.\d+)?)\s*{unit}", q)
            if m:
                return float(m.group(1))
    return None

def find_first_number_with_unit(query: str, unit: str) -> Optional[float]:
    m = re.search(rf"(\d+(?:\.\d+)?)\s*{unit}\b", query.lower())
    return float(m.group(1)) if m else None

def run_calculators(query: str, agent: str, frame: QueryFrame) -> List[str]:
    q = query.lower()
    results: List[str] = []
    # Reynolds number if values are explicitly provided.
    if "reynolds" in q or (agent == "cfd" and any(x in q for x in ["flow", "pipe", "duct"])):
        rho = extract_value(q, ["rho", "density"], ["kg/m3", "kg/m^3"])
        v = extract_value(q, ["v", "velocity"], ["m/s"])
        d = extract_value(q, ["d", "diameter"], ["m", "mm"])
        mu = extract_value(q, ["mu", "viscosity"], ["pa.s", "pas", "kg/ms"])
        if d is not None and "mm" in q and d > 0.02:
            d = d / 1000.0
        if all(x is not None for x in [rho, v, d, mu]) and mu != 0:
            Re = rho * v * d / mu
            regime = "laminar" if Re < 2300 else "transitional" if Re < 4000 else "turbulent"
            results.append(f"Reynolds number check: Re ≈ {Re:,.0f} → {regime} regime. Validate model choice and y+ target accordingly.")
        else:
            results.append("Reynolds calculator available, but missing density, velocity, diameter, or viscosity.")
    # Beam bending simple center point load if enough values.
    if "beam" in q or "deflection" in q:
        P = extract_value(q, ["p", "load"], ["n", "kn"])
        L = extract_value(q, ["l", "span"], ["mm", "m"])
        E = extract_value(q, ["e"], ["gpa", "mpa"])
        I = extract_value(q, ["i"], ["mm4", "mm^4", "m4", "m^4"])
        if P and L and E and I:
            if "kn" in q: P *= 1000
            if L > 10: L_m = L / 1000
            else: L_m = L
            E_pa = E * 1e9 if "gpa" in q else E * 1e6
            I_m4 = I * 1e-12 if "mm" in q else I
            delta = P * L_m**3 / (48 * E_pa * I_m4)
            results.append(f"Beam sanity check: center-load deflection δ ≈ {delta*1000:.3f} mm for simply supported beam assumptions.")
        else:
            results.append("Beam calculator available, but missing load P, span L, modulus E, or second moment I.")
    # Shaft torsion.
    if "shaft" in q or "torsion" in q:
        T = extract_value(q, ["t", "torque"], ["n.m", "nm", "n*m"])
        d = extract_value(q, ["d", "diameter"], ["mm", "m"])
        if T and d:
            d_m = d / 1000 if d > 0.05 else d
            tau = 16 * T / (math.pi * d_m**3)
            results.append(f"Shaft torsion sanity check: τ ≈ {tau/1e6:.1f} MPa for a solid circular shaft.")
        else:
            results.append("Shaft torsion calculator available, but missing torque and shaft diameter.")
    # Bearing L10.
    if "bearing" in q or "l10" in q:
        C = extract_value(q, ["c", "capacity"], ["n", "kn"])
        P = extract_value(q, ["p", "load"], ["n", "kn"])
        rpm = extract_value(q, ["rpm", "speed"], ["rpm"])
        if C and P and P != 0:
            if "kn" in q: C *= 1000; P *= 1000
            L10_mrev = (C/P)**3
            if rpm:
                hours = L10_mrev * 1e6 / (60 * rpm)
                results.append(f"Bearing L10 sanity check: L10 ≈ {hours:,.0f} hours using ball-bearing exponent 3.")
            else:
                results.append(f"Bearing L10 sanity check: L10 ≈ {L10_mrev:,.1f} million revolutions using ball-bearing exponent 3.")
        else:
            results.append("Bearing L10 calculator available, but missing dynamic capacity C and equivalent load P.")
    # Sheet metal bend allowance.
    if "bend allowance" in q or "sheet metal" in q:
        t = extract_value(q, ["t", "thickness"], ["mm"])
        r = extract_value(q, ["r", "radius"], ["mm"])
        angle = extract_value(q, ["angle", "a"], ["deg", "degree", "degrees"])
        k = extract_value(q, ["k", "k-factor"], [""])
        if t and r and angle:
            k = k if k else 0.33
            ba = math.radians(angle) * (r + k*t)
            results.append(f"Sheet metal bend allowance check: BA ≈ {ba:.2f} mm using K={k:.2f}.")
        else:
            results.append("Sheet-metal bend allowance calculator available, but missing thickness, bend radius, or angle.")
    if agent == "manufacturing" and ("injection" in q or "mold" in q or "cover" in q):
        if not re.search(r"\d+(?:\.\d+)?\s*mm", q):
            results.append("Injection molding wall/rib/boss validator: cannot run numeric check because nominal wall thickness was not provided.")
        else:
            t = find_first_number_with_unit(q, "mm")
            if t:
                status = "typical early range for many covers" if 1.5 <= t <= 3.5 else "requires material/process review"
                results.append(f"Injection molding wall-thickness check: detected {t:g} mm → {status}; verify by material grade, flow length, and surface class.")
    if not results:
        results.append("No deterministic calculator executed because the question lacks numerical inputs. The decision engine used rule-based assessment and missing-data detection.")
    return results

# =============================================================================
# Answer builder
# =============================================================================
def markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"]*len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(out)

def problem_frame_block(frame: QueryFrame) -> str:
    mats = ", ".join(frame.materials) if frame.materials else "not specified"
    qty = ", ".join(frame.quantities) if frame.quantities else "not specified"
    concepts = ", ".join(frame.concepts[:12]) if frame.concepts else "objective-specific engineering factors"
    notes = "\n".join(f"- {n}" for n in frame.intent_notes) if frame.intent_notes else "- No special routing note."
    return f"""### Problem frame
- Part/component: **{frame.part_type}**.
- Process/physics: **{frame.process}**.
- Materials detected: **{mats}**.
- Quantities detected: **{qty}**.
- Key concepts considered: {concepts}.
- Confidence: **{frame.confidence}**.

**Routing notes**
{notes}
"""

def protocol_block(agent: str) -> str:
    steps = PROTOCOLS.get(agent, PROTOCOLS["chief"])
    return "### Reasoning protocol applied\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))

def retrieval_block(hits: List[RetrievalHit]) -> str:
    if not hits:
        return "### Internal retrieval\nNo strong internal source matched. Add a knowledge pack or source document for this topic."
    rows = []
    for i, h in enumerate(hits[:6], 1):
        rows.append([f"K{i}", h.title, h.topic, h.confidence, f"{h.score:.1f}", f"`{h.path}`"])
    return "### Internal retrieval ranked by source relevance\n" + markdown_table(["ID", "Workspace", "Topic", "Confidence", "Score", "Source"], rows)

def scorecards_block(scorecards: List[ScoreCard]) -> str:
    if not scorecards:
        return "### Scoring engines\nNo specialized scoring engine was triggered for this question."
    parts = ["### Scoring engines"]
    for card in scorecards:
        parts.append(f"**{card.name}: {card.score}/100 — {card.level}**")
        rows = [[i.area, i.risk, i.reason, i.required_data, i.action] for i in card.items]
        parts.append(markdown_table(["Area", "Risk", "Reason", "Required data", "Action"], rows))
    return "\n\n".join(parts)

def recommendations_block(scorecards: List[ScoreCard], frame: QueryFrame) -> str:
    recs: List[str] = []
    for card in scorecards:
        recs.extend(card.recommendations)
    if frame.missing_data:
        recs.append("Collect missing release-critical inputs before design freeze.")
    recs = list(dict.fromkeys(recs))[:8]
    return "### Ranked recommendations\n" + "\n".join(f"{i}. {r}" for i, r in enumerate(recs, 1))

def calculators_block(results: List[str]) -> str:
    return "### Engineering calculators / deterministic checks\n" + "\n".join(f"- {r}" for r in results)

def missing_data_block(frame: QueryFrame) -> str:
    if not frame.missing_data:
        return "### Missing inputs\n- No major missing input was detected, but release still requires validation evidence."
    return "### Missing inputs detected\n" + "\n".join(f"- {x}" for x in frame.missing_data)

def assessment_block(agent: str, frame: QueryFrame, scorecards: List[ScoreCard]) -> str:
    if agent == "manufacturing":
        return """### Engineering assessment
For an injection-molded cover, treat the concept as **not release-ready** until material grade, wall thickness map, CAD geometry, production volume, cosmetic surface class, and assembly method are known. The highest early risks are wall-thickness uniformity, boss/rib design, gate/ejector/parting-line decisions, tolerance feasibility, and assembly method. The next technical move is not more styling; it is an evidence package: CAD/STEP, material, nominal wall, CTQs, and target volume.
"""
    if agent == "fea":
        return """### Engineering assessment
The simulation plan is not credible until the objective, load path, constraints, contacts, material model, mesh convergence strategy, and validation method are defined. Do not use stress plots as release evidence before checking reactions, deformation shape, convergence, and hand-calculation agreement.
"""
    if agent == "cfd":
        return """### Engineering assessment
The CFD setup is not credible until flow regime, fluid properties, boundary conditions, mesh/y+ strategy, convergence criteria, and analytical validation are defined. Start with Reynolds number, pressure-drop or heat-transfer estimates, then use CFD to refine—not replace—engineering judgment.
"""
    if agent == "materials":
        return """### Engineering assessment
Material selection should begin with functional constraints, not preferred materials. Screen candidates by hard constraints first, then rank by stiffness, strength, toughness, density, thermal limits, corrosion, process compatibility, cost, and availability. Final choice requires grade-specific datasheets.
"""
    if agent == "solidworks":
        return """### Engineering assessment
CAD automation should be treated as an engineering workflow, not just a macro. Define inputs, document type, units, output paths, overwrite rules, rebuild checks, and validation criteria before running automation on production files.
"""
    if agent == "patent":
        return """### Engineering assessment
Innovation work must separate the technical problem, inventive feature, closest prior art, implementation path, prototype test, and commercial advantage. Patentability cannot be asserted without prior-art review and professional legal assessment.
"""
    return """### Engineering assessment
This problem should be treated as a mechanical engineering decision with explicit assumptions, quantified checks where possible, internal references, missing data, and validation requirements before release.
"""

def compose_answer(query: str, agent: str, hits: List[RetrievalHit]) -> str:
    frame = build_query_frame(query, agent, hits)
    scorecards = build_scorecards(query, agent, frame)
    calc_results = run_calculators(query, agent, frame)
    title = f"## Mechanical Decision Engine v23 — {PACK_TITLES.get(WORKSPACE_TO_PACK.get(agent, ''), AGENTS.get(agent, 'General'))}"
    return "\n\n".join([
        title,
        problem_frame_block(frame),
        retrieval_block(hits),
        protocol_block(agent),
        scorecards_block(scorecards),
        assessment_block(agent, frame, scorecards),
        calculators_block(calc_results),
        missing_data_block(frame),
        recommendations_block(scorecards, frame),
        "### Engineering use note\nThis is internal engineering guidance from MechAI knowledge packs and deterministic reasoning. Verify calculations, standards compliance, CAD/simulation assumptions, safety factors, and test evidence before engineering release.",
    ])

# =============================================================================
# UI
# =============================================================================
st.set_page_config(page_title="MechAI Pro", page_icon="⚙️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
html,body,[data-testid="stAppViewContainer"],.stApp{background:#000!important;color:#f5f5f5!important;}
#MainMenu,footer,header{visibility:hidden!important;height:0!important;}
[data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"], button[kind="header"]{display:none!important;visibility:hidden!important;}
[data-testid="stSidebar"]{background:#050505!important;border-right:1px solid #222!important;min-width:292px!important;max-width:292px!important;width:292px!important;position:fixed!important;left:0!important;top:0!important;bottom:0!important;height:100vh!important;transform:none!important;visibility:visible!important;z-index:999!important;overflow-y:auto!important;}
.block-container{max-width:1050px!important;padding:2rem 2rem 8rem!important;margin-left:292px!important;}
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
.message-row{display:grid;grid-template-columns:40px minmax(0,1fr);gap:14px;margin:24px auto;max-width:980px;}
.avatar{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:15px;background:#232323;color:#fff;}
.avatar.user{background:#7c3aed}.avatar.ai{background:#202020;border:1px solid #333;}
.bubble{font-size:16px;line-height:1.72;color:#f4f4f4;overflow-wrap:anywhere;}
.bubble.user{font-weight:650;line-height:1.4;padding-top:3px;}
.agent-tag{color:#aaa;font-size:13px;margin-bottom:18px;}
.footer-note{position:fixed;left:292px;right:0;bottom:8px;text-align:center;color:#666;font-size:11px;pointer-events:none;}
[data-testid="stChatInput"]{position:fixed!important;left:calc(292px + 8vw)!important;right:8vw!important;bottom:32px!important;z-index:1001!important;background:#2b2b31!important;border:1px solid #3a3a42!important;border-radius:12px!important;padding:12px 14px!important;box-shadow:0 18px 40px rgba(0,0,0,.45)!important;}
[data-testid="stChatInput"] textarea{background:#212121!important;border:1px solid #3b3b3b!important;border-radius:999px!important;color:#f4f4f4!important;min-height:52px!important;padding:15px 58px 15px 20px!important;font-size:15px!important;}
[data-testid="stChatInput"] button{background:#f4f4f4!important;color:#000!important;border-radius:50%!important;width:38px!important;height:38px!important;}
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3{font-size:18px!important;line-height:1.65!important;margin-top:1rem!important;}
.stMarkdown p,.stMarkdown li{font-size:15.5px!important;line-height:1.7!important;}
.stMarkdown table{font-size:13px!important;border-collapse:collapse;width:100%;}
.stMarkdown th,.stMarkdown td{border-bottom:1px solid #222;padding:7px 8px;vertical-align:top;}
.stMarkdown code{font-size:12px!important;background:#161616!important;border:1px solid #2a2a2a!important;border-radius:5px!important;padding:1px 5px!important;}
@media(max-width:900px){[data-testid="stSidebar"]{position:relative!important;width:100%!important;max-width:100%!important;min-width:100%!important;height:auto!important}.block-container{margin-left:0!important;padding:1rem 1rem 8rem!important}[data-testid="stChatInput"]{left:1rem!important;right:1rem!important}.footer-note{left:0!important}.user-chip{position:static;width:auto;margin-top:18px}}
</style>
""", unsafe_allow_html=True)

seed_knowledge_packs()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "workspace" not in st.session_state:
    st.session_state.workspace = "chief"
if "view" not in st.session_state:
    st.session_state.view = "Chat"
if "project" not in st.session_state:
    st.session_state.project = "RD_Lab"

# Remove old messages generated by previous builds.
def is_old_message(msg: dict) -> bool:
    c = str(msg.get("content", ""))
    bad = ["OpenAI provider failed", "Gemini backup", "Knowledge Pack ##", "Internal knowledge retrieved:", "Mechanical Scientist Brain v22"]
    return any(x in c for x in bad)
if any(is_old_message(m) for m in st.session_state.messages):
    st.session_state.messages = []

with st.sidebar:
    st.markdown('<div class="sidebar-title">MechAI Pro</div>', unsafe_allow_html=True)
    if st.button("✎  New chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown('<div class="nav-btn">⌕&nbsp;&nbsp;Search chats</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-btn">▥&nbsp;&nbsp;Library</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-label">Workspace</div>', unsafe_allow_html=True)
    keys = list(WORKSPACES.keys())
    labels = [WORKSPACES[k] for k in keys]
    idx = keys.index(st.session_state.workspace) if st.session_state.workspace in keys else 0
    selected = st.selectbox("Workspace", labels, index=idx, label_visibility="collapsed")
    st.session_state.workspace = keys[labels.index(selected)]
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
        st.caption("Brain: Mechanical Decision Engine v23")
        st.caption(f"Internal knowledge chunks: {len(load_chunks())}")
        st.caption(f"Reasoning protocols: {len(PROTOCOLS)}")
        st.caption("Scoring engines: DFM, DFA, FEA, CFD, Materials, CAD, Patent")
        st.caption("Engineering calculators: beam, shaft, bearing, Reynolds, pressure drop, bend allowance, injection checks")
        st.caption("External providers are not part of this build.")
        st.caption(f"Build: {BUILD_ID}")
    st.markdown('<div class="user-chip">Wafeeq · MechAI Pro</div>', unsafe_allow_html=True)

if st.session_state.view == "About":
    st.markdown(f"""
**MechAI Pro — Mechanical Decision Engine v23**

This build executes the first five strategic requirements in one release:

1. **Deep Knowledge Packs** for Mechanical Design, CAD/SolidWorks, FEA, CFD/Thermal, Manufacturing/DFM, Materials, and Innovation/Patent.
2. **Reasoning Engine** with risk classification, missing-data detection, confidence, assumptions, and recommendation ranking.
3. **Scoring Engines** for DFM, DFA, FEA setup, CFD setup, materials suitability, CAD automation risk, and patent readiness.
4. **Engineering Calculators** for deterministic sanity checks when numerical inputs are present.
5. **Improved Retrieval Engine** with markdown chunking, workspace metadata, source ranking, source confidence, and internal citations.

External AI providers are not part of the reference brain.

**Build:** `{BUILD_ID}`
""")
else:
    if not st.session_state.messages:
        st.markdown('<div class="landing"><h1>Good to see you, Wafeeq.</h1></div>', unsafe_allow_html=True)
    else:
        for m in st.session_state.messages:
            role = m.get("role", "assistant")
            content = str(m.get("content", ""))
            agent = m.get("agent", "chief")
            if role == "user":
                st.markdown(f'<div class="message-row"><div class="avatar user">☻</div><div class="bubble user">{html.escape(content)}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="message-row"><div class="avatar ai">⚙</div><div class="bubble ai"><div class="agent-tag">{html.escape(AGENTS.get(agent, AGENTS["chief"]))} · Internal Knowledge Only · Mechanical Decision Engine v23</div>', unsafe_allow_html=True)
                st.markdown(content)
                st.markdown('</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="footer-note">MechAI Pro · Mechanical Decision Engine v23 · Internal Knowledge Only · Verify all outputs before engineering release</div>', unsafe_allow_html=True)

user_prompt = st.chat_input("Ask anything engineering…")
if user_prompt:
    selected_ws = st.session_state.workspace
    agent = route_agent(user_prompt, selected_ws)
    hits = retrieve_knowledge(user_prompt, agent, top_k=7)
    answer = compose_answer(user_prompt, agent, hits)
    st.session_state.messages.append({"role": "user", "content": user_prompt, "agent": agent})
    st.session_state.messages.append({"role": "assistant", "content": answer, "agent": agent})
    st.rerun()
