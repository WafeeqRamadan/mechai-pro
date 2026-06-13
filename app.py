# -*- coding: utf-8 -*-
"""
MechAI Pro v25 — Full Mechanical Engineering OS Core
====================================================
Knowledge-first mechanical engineering assistant.

What this build includes:
1) Deep Engineering Knowledge Library seeds for all workspaces.
2) Mechanical Reasoning Engine with routing, ontology, missing-data detection, confidence logic.
3) Engineering Calculators & Validators.
4) Project Memory & Engineering History.
5) CAD / SolidWorks Automation Bridge foundation: macro generation, validation, .bas export.
6) FEA / CFD Simulation Intelligence: setup scoring, APDL/Fluent starter export.
7) Reports & Engineering Outputs: Markdown, DOCX, PDF, XLSX.
8) Legal/Private Knowledge Ingestion for user-owned/public references.
9) Evaluation & Quality Testing System.
10) Production-grade Streamlit UI foundation.

No OpenAI/Gemini dependency in this build. External AI can be added later as an optional tool.
"""
from __future__ import annotations

import csv
import html
import io
import json
import math
import os
import re
import shutil
import textwrap
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import streamlit as st

try:
    import PyPDF2  # type: ignore
except Exception:  # pragma: no cover
    PyPDF2 = None

try:
    from docx import Document  # type: ignore
except Exception:  # pragma: no cover
    Document = None

try:
    from reportlab.lib.pagesizes import A4  # type: ignore
    from reportlab.pdfgen import canvas  # type: ignore
except Exception:  # pragma: no cover
    A4 = None
    canvas = None

try:
    from openpyxl import Workbook  # type: ignore
except Exception:  # pragma: no cover
    Workbook = None

APP_VERSION = "v25_FULL_MECHANICAL_ENGINEERING_OS_2026_06_13"
APP_TITLE = "MechAI Pro"
ROOT = Path(__file__).resolve().parent
KNOWLEDGE_DIR = ROOT / "knowledge_packs"
PROJECT_MEMORY_DIR = ROOT / "project_memory"
EXPORT_DIR = ROOT / "exports"

PROJECT_MEMORY_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

WORKSPACES = {
    "General engineering": {"icon": "🧠", "folder": None, "agent": "Chief Mechanical Scientist"},
    "Product R&D / Design": {"icon": "🛠️", "folder": "mechanical_design", "agent": "Mechanical Design Scientist"},
    "CAD / SolidWorks": {"icon": "🧩", "folder": "cad_solidworks", "agent": "CAD / SolidWorks Automation Scientist"},
    "Simulation / FEA": {"icon": "📊", "folder": "simulation_fea", "agent": "FEA Simulation Scientist"},
    "CFD / Thermal": {"icon": "🌊", "folder": "cfd_thermal", "agent": "CFD / Thermal Scientist"},
    "Manufacturing / DFM": {"icon": "🏭", "folder": "manufacturing_dfm", "agent": "Manufacturing DFM/DFA Scientist"},
    "Materials Selection": {"icon": "🧪", "folder": "materials_selection", "agent": "Materials Selection Scientist"},
    "Innovation / Patent": {"icon": "💡", "folder": "innovation_patent", "agent": "Innovation / Patent Scientist"},
}

# -----------------------------------------------------------------------------
# Deep Knowledge Library Seeds
# -----------------------------------------------------------------------------

KNOWLEDGE_SEED: Dict[str, Dict[str, str]] = {
    "mechanical_design": {
        "beams.md": """
# Beams — Mechanical Design Expert Pack

## Scope
Beam bending, shear, deflection, stiffness, support conditions, preliminary sizing, and validation.

## Required inputs
- Load case: point load, distributed load, moment, combined loading.
- Support condition: simply supported, cantilever, fixed-fixed, overhung.
- Span length, cross-section geometry, material modulus, yield strength.
- Deflection limit, safety factor, environment, manufacturing process.

## Core equations and checks
- Bending stress: sigma = M*c/I.
- Shear stress check depends on section; rectangular approximation tau_max = 1.5V/A.
- Center point load simply supported: Mmax = P*L/4, deflection = P*L^3/(48EI).
- Cantilever end load: Mmax = P*L, deflection = P*L^3/(3EI).
- Always check both strength and stiffness; many beam designs fail by excessive deflection before yield.

## Decision logic
- If load path is unclear, confidence is low.
- If only force is known but support and geometry are missing, request support and cross-section.
- If deflection tolerance is critical, rank stiffness before stress.
- If cyclic load exists, switch to fatigue reasoning.

## Failure modes
Yielding, buckling, excessive deflection, vibration, local stress concentration, weld/joint failure.

## Validation
Compare hand calculation with FEA or physical test. Confirm load cases and boundary conditions before release.
""",
        "shafts.md": """
# Shafts — Mechanical Design Expert Pack

## Scope
Rotating or stationary shafts under torque, bending, axial load, fatigue, keyways, bearing seats, and critical speed.

## Required inputs
Torque, speed, bending moment, support/bearing layout, diameter constraints, material, surface finish, keyways/splines, duty cycle.

## Core equations and checks
- Solid circular torsion shear: tau_max = 16T/(pi*d^3).
- Angle of twist: theta = T*L/(J*G), J = pi*d^4/32 for solid shaft.
- Combined bending/torsion needs equivalent stress such as von Mises or fatigue criteria.
- Keyways reduce fatigue strength and introduce stress concentration.

## Decision logic
- If shaft transmits power, compute torque from P = T*omega.
- If keyway exists, increase fatigue risk.
- If high speed, evaluate critical speed and balancing.
- If bearings are close to load, check bearing reaction and deflection.

## Failure modes
Torsional yielding, bending fatigue, fretting at bearing seats, keyway crack initiation, excessive twist, resonance.

## Validation
Hand calculations, fatigue estimate, bearing life, deflection check, prototype run-out/vibration test.
""",
        "bearings.md": """
# Bearings — Mechanical Design Expert Pack

## Scope
Bearing selection, L10 life, load ratings, shaft/housing fits, lubrication, contamination, speed and temperature limits.

## Required inputs
Radial load, axial load, speed, desired life, bearing type, load spectrum, lubrication, temperature, contamination level.

## Core equations and checks
- Basic rating life: L10 = (C/P)^p million revolutions; p=3 for ball bearings, p=10/3 for roller bearings.
- Life hours: L10h = 1e6/(60*n) * (C/P)^p.
- Equivalent dynamic load depends on bearing type and axial/radial ratio.

## Decision logic
- If load spectrum is unknown, confidence is low.
- If contamination or poor lubrication exists, apply service factors.
- Check fit: rotating inner ring usually needs interference on shaft.
- Confirm speed, temperature, and sealing.

## Failure modes
Fatigue spalling, overheating, lubrication starvation, contamination wear, brinelling, misalignment.

## Validation
Supplier rating, equivalent load calculation, thermal check, lubrication plan, bearing installation review.
""",
        "gears.md": """
# Gears — Mechanical Design Expert Pack

## Scope
Preliminary gear selection, gear ratio, torque transfer, tooth bending, pitting, lubrication and manufacturability.

## Required inputs
Power, speed, ratio, torque, gear type, module/DP, face width, material, heat treatment, duty cycle, noise target.

## Core checks
- Torque from power and angular speed.
- Tooth bending strength and contact stress require geometry factors.
- Face width, pressure angle, module, tooth count and center distance must be consistent.
- Avoid undercut for low tooth counts.

## Decision logic
- If high shock load, increase service factor.
- If quiet operation needed, consider helical gears and surface finish.
- If compact gearbox, check thermal and lubrication limits.

## Failure modes
Tooth bending fracture, pitting, scuffing, wear, noise, misalignment, lubrication failure.

## Validation
AGMA/ISO-style detailed check, contact pattern inspection, prototype endurance/noise test.
""",
        "springs.md": """
# Springs — Mechanical Design Expert Pack

## Scope
Compression/extension/torsion springs, stiffness, deflection, fatigue, buckling, solid height, material and manufacturing constraints.

## Required inputs
Load range, required deflection, available envelope, cycle life, temperature, material, end style.

## Core checks
- Spring rate depends on wire diameter, mean coil diameter, active coils and shear modulus.
- Check solid height and maximum stress.
- Fatigue is critical for cyclic springs.
- Compression springs may buckle if slender.

## Decision logic
- If cyclic duty is high, prioritize fatigue safety.
- If temperature is high, verify material relaxation/creep.
- If envelope is tight, check solid height and coil bind.

## Failure modes
Fatigue fracture, set/relaxation, buckling, corrosion, coil bind.

## Validation
Load-deflection test, cycle test, dimensional inspection.
""",
        "fasteners.md": """
# Fasteners — Mechanical Design Expert Pack

## Scope
Bolted joints, screw selection, preload, clamp force, thread engagement, loosening, fatigue and assembly process.

## Required inputs
Joint function, external loads, bolt size/grade, material stack, friction/lubrication, torque method, vibration, temperature.

## Core checks
- Preload is the primary design variable for bolted joints.
- Torque is a noisy proxy for preload due to friction variability.
- Thread engagement in soft materials must be checked.
- Joint separation and slip must be avoided when preload is functional.

## Decision logic
- If vibration exists, add locking strategy and joint stiffness review.
- If plastic bosses are used, avoid over-torque and check creep.
- If safety-critical, specify controlled tightening method.

## Failure modes
Loosening, thread stripping, fatigue, creep relaxation, joint separation, galvanic corrosion.

## Validation
Torque-tension testing, pull-out test, vibration test, assembly audit.
""",
        "fatigue.md": """
# Fatigue — Mechanical Design Expert Pack

## Scope
High-cycle and low-cycle fatigue, stress concentrations, surface finish, mean stress, notch sensitivity and validation.

## Required inputs
Load cycle, stress amplitude, mean stress, material fatigue data, surface finish, size, temperature, environment, notches.

## Core logic
- Fatigue risk increases with cyclic stress, notches, tensile mean stress, poor finish, corrosion and temperature.
- Static yield safety does not guarantee fatigue safety.
- Stress concentration at keyways, threads, sharp corners and weld toes must be included.

## Decision logic
- If cyclic load exists and geometry has notches, route to fatigue review.
- If no S-N data exists, confidence is limited.
- Use conservative assumptions before test validation.

## Failure modes
Crack initiation at stress raisers, crack growth, sudden fracture.

## Validation
Fatigue calculation, FEA hotspot review, endurance test, inspection plan.
""",
        "gdnt_tolerances.md": """
# GD&T and Tolerances — Mechanical Design Expert Pack

## Scope
Functional tolerancing, datum strategy, fits, stack-up, manufacturability, inspection and assembly compatibility.

## Required inputs
Functional interfaces, datum features, critical dimensions, mating parts, manufacturing process, inspection method.

## Core rules
- Tolerances must be tied to function, not arbitrary precision.
- Over-tight tolerances increase cost and scrap.
- Datum scheme must reflect assembly and inspection reality.
- Tolerance stack-up must be checked for critical assemblies.

## Decision logic
- If tolerance is critical but process is unknown, risk is high.
- If inspection method is missing, release readiness is low.
- GD&T should control form/orientation/location according to functional need.

## Failure modes
Assembly interference, excessive clearance, inspection ambiguity, high scrap, supplier disputes.

## Validation
Tolerance stack-up, gauge/inspection plan, process capability check.
""",
    },
    "manufacturing_dfm": {
        "injection_molding_expert.md": """
# Injection Molding Expert Pack

## Scope
DFM for thermoplastic injection molded parts: wall thickness, draft, ribs, bosses, gates, ejectors, shrinkage, sink marks, warpage, tooling and production stability.

## Required inputs
Material grade, nominal wall thickness, CAD geometry, part function, surface class, annual volume, tolerances, assembly method, inserts/snap-fits.

## Core rules
- Keep wall thickness as uniform as possible.
- Avoid thick bosses and thick intersections; they create sink, voids and long cycle time.
- Add draft to vertical walls, ribs and bosses to allow clean ejection.
- Ribs should stiffen without becoming thick solid sections.
- Gate location affects flow, weld lines, packing, shrinkage and appearance.
- Ejector placement must avoid cosmetic damage and deformation.

## Decision logic
- If material is unknown, confidence is low-to-medium.
- If wall thickness is unknown, wall/sink/warpage risk is high.
- If CAD is absent, review is preliminary.
- If surface class is high, gate, ejector and parting line risk rises.

## Red flags
Sharp internal corners, thick bosses, no draft, uneven walls, isolated heavy sections, deep ribs, uncontrolled snap-fit tolerance.

## Validation
Moldflow or simplified filling review, prototype tooling or trial shot, dimensional inspection, sink/warpage review, assembly trial.
""",
        "sheet_metal_expert.md": """
# Sheet Metal Expert Pack

## Scope
Sheet metal DFM: bends, bend radius, K-factor, reliefs, holes near bends, flanges, flat pattern, tolerances and forming limits.

## Required inputs
Material, thickness, bend radius, bend angle, grain direction, tooling, surface finish, hole/flange geometry, flat pattern requirement.

## Core rules
- Internal bend radius should be compatible with material and thickness.
- Holes/slots near bends can distort and need minimum distance.
- Bend relief prevents tearing at flange ends.
- Tolerances across multiple bends accumulate.
- Flat pattern must use appropriate K-factor/bend allowance.

## Decision logic
- If thickness or bend radius missing, bend feasibility is uncertain.
- If tight tolerance across bends, process capability risk increases.
- If cosmetic surface, tooling marks and grain direction matter.

## Validation
Flat pattern review, bend trial, first article inspection, gauge strategy.
""",
        "machining_expert.md": """
# Machining Expert Pack

## Scope
CNC/machining DFM: tool access, setups, tolerances, surface finish, fixturing, material machinability and cycle time.

## Required inputs
Material, stock form, tolerances, surface finish, quantity, machine type, datum/fixturing, tool access constraints.

## Core rules
- Reduce number of setups and reorientations.
- Avoid unnecessarily tight tolerances and deep narrow pockets.
- Internal radii must match tool availability.
- Datum strategy must support fixturing and inspection.
- Surface finish requirements affect process time and tooling.

## Decision logic
- If tolerance is tighter than process capability, risk is high.
- If deep pockets or small radii exist, tooling/cycle risk is high.
- If datum scheme unclear, inspection and repeatability risk rise.

## Validation
CAM review, tool access review, setup sheet, first article inspection.
""",
        "assembly_dfa_expert.md": """
# Assembly / DFA Expert Pack

## Scope
Design for assembly: part count, fasteners, orientation, handling, mistake-proofing, access, serviceability and assembly cost.

## Required inputs
Assembly sequence, mating parts, fasteners, operator/automation method, access constraints, service requirements, production volume.

## Core rules
- Reduce part count where possible.
- Prefer self-locating features and one-way assembly.
- Avoid hidden fasteners and poor tool access.
- Use common fastener sizes and minimize tool changes.
- Consider poka-yoke for orientation-sensitive parts.

## Decision logic
- If assembly sequence is unknown, DFA confidence is low.
- If fastener count is high, cost and error risk increase.
- If snap-fits are used, material creep and tolerance sensitivity must be checked.

## Validation
Assembly trial, time study, operator feedback, service/disassembly review.
""",
        "tolerance_capability_expert.md": """
# Tolerance and Process Capability Expert Pack

## Scope
Tolerance feasibility, process capability, Cp/Cpk thinking, inspection strategy and cost impact.

## Required inputs
Critical dimensions, tolerance values, manufacturing process, material, inspection method, supplier capability, volume.

## Core rules
- Tight tolerances must be justified by function.
- Process capability must match tolerance requirement.
- Dimensional stability depends on material, process and environment.
- Inspection method must resolve tolerance reliably.

## Decision logic
- If tolerance is specified but process is unknown, risk is high.
- If tolerance is cosmetic/non-functional, recommend relaxation.
- If high volume, capability and gauge repeatability become critical.

## Validation
Capability study, gauge R&R, first article inspection, tolerance stack-up.
""",
        "cost_reduction_expert.md": """
# Cost Reduction Expert Pack

## Scope
Cost-down engineering: material, process, tooling, cycle time, scrap, assembly effort, inspection and supplier complexity.

## Required inputs
Volume, current process, material cost, cycle time, part count, scrap rate, tooling assumptions, quality requirements.

## Cost drivers
- Material mass and grade.
- Cycle time and machine rate.
- Tooling complexity and maintenance.
- Scrap/rework.
- Assembly labor and fasteners.
- Inspection burden.

## Decision logic
- Rank recommendations by risk reduction, cost impact and implementation ease.
- Avoid cost reduction that increases field failure risk.
- Prefer geometry simplification and tolerance relaxation before changing material blindly.

## Validation
Cost model, supplier quote, pilot run, quality impact review.
""",
        "quality_control_expert.md": """
# Quality Control Expert Pack

## Scope
Quality planning, inspection, CTQ dimensions, defect modes, sampling, first article and production stability.

## Required inputs
Critical-to-quality features, tolerance limits, defect risks, inspection tools, production volume, supplier process.

## Core rules
- Identify CTQ features based on function and assembly.
- Match inspection method to tolerance and geometry.
- High-risk defects need prevention and detection controls.
- Quality plan should connect failure modes to inspection actions.

## Decision logic
- If CTQ features are unknown, release readiness is low.
- If inspection is not defined, tolerance control is incomplete.
- If defect risk is high, add process controls and validation tests.

## Validation
Control plan, FAI, capability study, incoming inspection, production audit.
""",
    },
    "materials_selection": {
        "thermoplastics.md": """
# Thermoplastics Expert Pack

## Scope
Selection of ABS, PP, PE, PC, PA, POM, PET, PBT, PEEK and blends for molded/mechanical parts.

## Required inputs
Function, load, temperature, chemical exposure, impact, stiffness, cosmetic needs, process, cost target, regulatory constraints.

## Core rules
- ABS is common for cosmetic enclosures but has limited heat/chemical resistance.
- PP is chemically resistant and low density but lower stiffness.
- PC has high impact resistance but needs drying and careful molding.
- PA absorbs moisture and dimensions can change.
- PEEK is high performance but expensive.

## Decision logic
- If temperature is high, screen out low-heat plastics.
- If snap-fits are used, toughness and fatigue matter.
- If tight tolerance, moisture absorption and shrinkage matter.

## Validation
Supplier datasheet, prototype molding, mechanical testing, environmental exposure.
""",
        "metals.md": """
# Metals Expert Pack

## Scope
Steel, stainless steel, aluminum, brass, cast alloys and heat-treated metals for mechanical design.

## Required inputs
Load, stiffness, fatigue, corrosion, temperature, mass target, process, surface finish, cost and availability.

## Core rules
- Steel offers strength and stiffness but higher density and corrosion risk.
- Aluminum reduces mass but has lower modulus and different fatigue behavior.
- Stainless improves corrosion resistance but may increase cost and machining difficulty.
- Heat treatment affects strength, toughness and distortion.

## Decision logic
- If stiffness drives design, modulus matters more than yield strength.
- If corrosion exists, material and coating must be considered together.
- If fatigue exists, surface finish and stress concentration are critical.

## Validation
Material certification, mechanical testing, corrosion testing, process validation.
""",
        "elastomers.md": """
# Elastomers Expert Pack

## Scope
Rubber/elastomer selection for seals, vibration isolation, grips and flexible components.

## Required inputs
Fluid exposure, temperature, compression set, hardness, load, motion, UV/ozone, manufacturing method.

## Core rules
- Hardness is not enough; compression set, chemical resistance and temperature are critical.
- NBR is common for oils; EPDM for weather/water; silicone for temperature; FKM for chemicals/heat.
- Seal design must consider squeeze, groove fill and tolerance stack.

## Decision logic
- If fluid is unknown, material confidence is low.
- If sealing is critical, groove and compression data are required.

## Validation
Compression set test, leak test, aging exposure, assembly trial.
""",
        "corrosion.md": """
# Corrosion Expert Pack

## Scope
Corrosion risk screening, galvanic compatibility, coatings, environment and lifecycle.

## Required inputs
Material pair, electrolyte/environment, temperature, coating, exposure duration, maintenance plan.

## Core rules
- Galvanic corrosion requires dissimilar metals and electrolyte.
- Coatings can fail at scratches and edges.
- Crevices trap electrolyte and increase risk.

## Decision logic
- If outdoor/marine/chemical exposure exists, corrosion must be explicit.
- If dissimilar metals contact, check galvanic isolation.

## Validation
Salt spray/chemical exposure, coating spec, field environment review.
""",
        "temperature_limits.md": """
# Temperature Limits Expert Pack

## Scope
Temperature screening for plastics, metals, elastomers and assemblies.

## Required inputs
Operating temperature, peak temperature, duration, load at temperature, environment, safety margin.

## Core rules
- Plastics lose stiffness with temperature and may creep.
- Elastomers degrade or take compression set outside their range.
- Thermal expansion can dominate tolerance stack-up.

## Decision logic
- If load is sustained at temperature, creep/relaxation must be checked.
- If materials have different CTE, interface stress and clearance change matter.

## Validation
Thermal cycling, heat aging, dimensional inspection, functional test at temperature.
""",
        "ashby_selection_logic.md": """
# Ashby Selection Logic Expert Pack

## Scope
Structured material selection using functional requirements, constraints, objectives and free variables.

## Process
1. Translate design need into function, constraints, objective and free variables.
2. Screen materials that violate hard constraints.
3. Rank remaining materials by objective: cost, mass, stiffness, strength, thermal performance.
4. Validate manufacturability and supply.

## Decision logic
- Never select material from a single property.
- Separate constraints from objectives.
- Include process compatibility and supplier availability.

## Validation
Datasheet review, prototype testing, supplier confirmation, lifecycle risk review.
""",
    },
    "simulation_fea": {
        "static_structural.md": """
# Static Structural FEA Expert Pack

## Scope
Static stress/deflection simulation setup for mechanical components and assemblies.

## Required inputs
Objective, geometry, material, loads, constraints, contacts, mesh strategy, acceptance criteria.

## Core rules
- Boundary conditions dominate results.
- Loads and constraints must represent physical reality.
- Contacts need careful stiffness/friction assumptions.
- Mesh convergence is mandatory for release-critical stress.

## Decision logic
- If material is missing, setup readiness is low.
- If constraints are unrealistic, results can be misleading.
- If only stress plot exists without convergence, confidence is low.

## Validation
Hand calculation, benchmark, mesh convergence, test correlation.
""",
        "modal_analysis.md": """
# Modal Analysis Expert Pack

## Scope
Natural frequencies, mode shapes, resonance avoidance and boundary condition sensitivity.

## Required inputs
Mass distribution, stiffness, constraints, operational excitation frequencies, damping assumptions.

## Core rules
- Modal results are highly sensitive to constraints and mass representation.
- Compare natural frequencies with excitation frequencies and harmonics.
- Mode shape interpretation matters more than frequency alone.

## Validation
Tap test, accelerometer data, operational vibration measurements.
""",
        "buckling.md": """
# Buckling FEA Expert Pack

## Scope
Linear eigenvalue buckling and nonlinear post-buckling reasoning for slender structures.

## Required inputs
Geometry, compressive load path, imperfections, material, constraints, load eccentricity.

## Core rules
- Linear buckling often overestimates capacity.
- Imperfections and eccentricity matter.
- Slender structures may fail by instability before material yield.

## Validation
Hand Euler estimate, nonlinear analysis, physical compression test.
""",
        "fatigue_fea.md": """
# Fatigue FEA Expert Pack

## Scope
Fatigue assessment using stress results, load cycles, mean stress, notch effects and material data.

## Required inputs
Stress amplitude, mean stress, S-N or strain-life data, surface finish, notch, environment, cycle count.

## Core rules
- Fatigue needs cyclic load definition; static FEA alone is insufficient.
- Hotspot stress should be mesh-insensitive.
- Surface finish and notches affect fatigue significantly.

## Validation
Fatigue calculation, endurance testing, inspection plan.
""",
        "contacts.md": """
# Contacts Expert Pack

## Scope
Contact modeling in FEA: bonded, frictionless, frictional, no-separation and nonlinear contact behavior.

## Required inputs
Contact surfaces, expected separation/sliding, friction, preload, contact stiffness, mesh density near interface.

## Core rules
- Wrong contact type can completely change load path.
- Frictional contact increases nonlinearity and convergence difficulty.
- Contact pressure requires refined mesh and realistic constraints.

## Validation
Contact sensitivity study, load path review, physical interface inspection.
""",
        "mesh_convergence.md": """
# Mesh Convergence Expert Pack

## Scope
Mesh independence, local refinement, stress singularities and result credibility.

## Required inputs
Quantity of interest, mesh sizes, element type, geometry features, stress concentration zones.

## Core rules
- Refine mesh until engineering quantity stabilizes.
- Ignore singular stress peaks at idealized sharp constraints unless physically meaningful.
- Use local refinement near stress raisers and contacts.

## Validation
Convergence plot, independent hand estimate, sensitivity studies.
""",
        "validation.md": """
# FEA Validation Expert Pack

## Scope
Verification and validation strategy for simulation credibility.

## Core rules
- Verification: solve the equations correctly.
- Validation: solve the right physical problem.
- Every release-critical simulation needs a validation plan.

## Evidence types
Hand calculations, benchmark problems, test data, mesh convergence, sensitivity studies, peer review.
""",
    },
    "cfd_thermal": {
        "internal_flow.md": """
# Internal Flow Expert Pack

## Scope
Pipe/duct/channel flow, pressure drop, Reynolds number, entrance effects and thermal-fluid checks.

## Required inputs
Fluid, density, viscosity, diameter/hydraulic diameter, velocity/flow rate, length, roughness, temperature.

## Core rules
- Reynolds number classifies flow regime.
- Pressure drop depends on friction factor, length, diameter, velocity and fittings.
- Entrance length matters in short channels.
- For heat transfer, Prandtl and Nusselt correlations may be needed.

## Validation
Mass balance, pressure measurement, analytical estimate, grid sensitivity.
""",
        "external_flow.md": """
# External Flow Expert Pack

## Scope
Flow around bodies, drag, boundary layers, separation, wake and cooling.

## Required inputs
Geometry, free-stream velocity, fluid properties, turbulence intensity, domain size, boundary conditions.

## Core rules
- Domain size and boundary placement affect results.
- Mesh near walls and separation regions is critical.
- Validate drag/pressure trends with correlations or test data.
""",
        "reynolds_number.md": """
# Reynolds Number Expert Pack

## Scope
Flow regime classification using Re = rho*V*D/mu.

## Required inputs
Density, velocity, characteristic length/diameter, dynamic viscosity.

## Logic
- Pipe flow: laminar typically Re < 2300, transitional around 2300-4000, turbulent above that.
- Use regime to choose model and correlations.

## Missing data
If density, viscosity, velocity or length are missing, do not classify with confidence.
""",
        "turbulence_models.md": """
# Turbulence Models Expert Pack

## Scope
Choosing laminar, k-epsilon, k-omega SST, transitional and wall treatment approaches.

## Core rules
- Use laminar only if regime and physics justify it.
- k-omega SST is often robust for adverse pressure gradients and near-wall effects.
- Wall treatment requires y+ compatibility.
- Model choice must be justified by flow physics, not default settings.
""",
        "y_plus.md": """
# y+ Expert Pack

## Scope
Near-wall mesh quality and turbulence model wall treatment.

## Core rules
- Low-Re wall-resolved models generally need y+ near 1.
- Wall functions typically need larger y+ ranges depending on solver guidance.
- Inflation layers should resolve boundary layer gradients.

## Validation
Check y+ contours after solution and adjust mesh accordingly.
""",
        "pressure_drop.md": """
# Pressure Drop Expert Pack

## Scope
Pressure loss in internal flows, fittings and channels.

## Core equations
- Darcy-Weisbach: DeltaP = f*(L/D)*(rho*V^2/2).
- Minor losses: DeltaP = K*(rho*V^2/2).

## Required inputs
Friction factor or roughness, length, diameter, velocity, density, fittings.
""",
        "heat_transfer.md": """
# Heat Transfer Expert Pack

## Scope
Conduction, convection, radiation, heat sinks, thermal resistance and transient heat-up.

## Required inputs
Heat load, geometry, material conductivity, fluid conditions, boundary conditions, ambient temperature.

## Core rules
- Use thermal resistance networks for first estimates.
- Convective coefficient uncertainty often dominates simple thermal models.
- For electronics cooling, junction-to-ambient path matters.

## Validation
Thermocouple/IR test, energy balance, sensitivity study.
""",
    },
    "cad_solidworks": {
        "macro_generation.md": """
# SolidWorks Macro Generation Expert Pack

## Scope
Generating safe, structured VBA macros for SolidWorks automation.

## Required inputs
Task, file types, folder paths, overwrite policy, document type, naming rules, error handling requirements.

## Core rules
- Always get active SolidWorks application and active document safely.
- Validate document type before executing operations.
- Avoid destructive file overwrite unless explicitly allowed.
- Provide clear run instructions and backup warning.

## Macro structure
1. Declarations and constants.
2. Get SldWorks application.
3. Validate active document.
4. Execute task.
5. Error handler.
6. User-visible completion message.
""",
        "solidworks_vba_patterns.md": """
# SolidWorks VBA Patterns Expert Pack

## Scope
Common VBA automation patterns for SolidWorks.

## Patterns
- Active document validation.
- Iterating configurations or drawings.
- Exporting STEP/PDF/DXF.
- Handling paths and filenames.
- Showing status messages.

## Safety
Use explicit variables, error handling, and non-destructive defaults.
""",
        "feature_creation.md": """
# Feature Creation Expert Pack

## Scope
Creating sketches, extrudes, cuts, revolves and reference geometry programmatically.

## Core rules
- Use parametric dimensions.
- Name sketches/features clearly.
- Use units explicitly.
- Separate sketch creation from feature creation.
""",
        "drawing_automation.md": """
# Drawing Automation Expert Pack

## Scope
Automated drawing creation, view placement, dimensions, annotations and export.

## Required inputs
Template path, sheet size, views, scale, title block data, export format.

## Risk
Drawing automation is sensitive to templates and standards; validate output manually.
""",
        "bom_export.md": """
# BOM Export Expert Pack

## Scope
Bill of materials export and metadata extraction.

## Required inputs
Assembly path, configurations, BOM template, output path, part properties.

## Core rules
Validate custom properties and configuration-specific data before release.
""",
        "dxf_step_export.md": """
# DXF/STEP Export Expert Pack

## Scope
Exporting parts, assemblies and sheet metal flat patterns.

## Core rules
- Validate document type.
- For sheet metal DXF, ensure flat pattern exists.
- Check output folder and overwrite policy.
- Log exported filenames.
""",
        "macro_validation.md": """
# Macro Validation Expert Pack

## Scope
Checking macro safety and execution readiness.

## Checklist
- Active document validation.
- File path validation.
- Error handler present.
- Overwrite policy explicit.
- User instructions included.
- Backup warning included.
""",
    },
    "innovation_patent": {
        "idea_evaluation.md": """
# Idea Evaluation Expert Pack

## Scope
Evaluating engineering ideas for novelty, usefulness, feasibility, manufacturability and business value.

## Required inputs
Problem, current alternatives, user benefit, technical principle, prototype concept, manufacturing process, target market.

## Core rules
Separate invention value into novelty, utility, feasibility, cost and defensibility.
""",
        "triz_methods.md": """
# TRIZ Methods Expert Pack

## Scope
Contradiction solving, inventive principles and systematic innovation.

## Core logic
Identify contradiction: improving one parameter worsens another. Generate concepts using separation principles and inventive patterns.
""",
        "prior_art_search.md": """
# Prior Art Search Expert Pack

## Scope
Planning prior-art searches across patents, products, papers and public disclosures.

## Core rules
Search by function, mechanism, keywords, classification and synonyms. Document closest references.
""",
        "claim_structure.md": """
# Claim Structure Expert Pack

## Scope
High-level claim thinking for inventions. Not legal advice.

## Core rules
Claims should focus on essential technical features and distinguish from prior art. Patent attorney review is required.
""",
        "prototype_strategy.md": """
# Prototype Strategy Expert Pack

## Scope
Prototype planning, MVP tests, failure discovery and validation roadmaps.

## Core rules
Prototype to reduce uncertainty, not to look finished. Define test objective before building.
""",
        "novelty_risk.md": """
# Novelty Risk Expert Pack

## Scope
Assessing novelty uncertainty before patent investment.

## Risk factors
Known similar products, obvious combination, public disclosure, weak technical distinction.
""",
    },
}

# -----------------------------------------------------------------------------
# Data models
# -----------------------------------------------------------------------------

@dataclass
class SourceChunk:
    workspace: str
    source: str
    title: str
    text: str
    score: float
    source_type: str = "knowledge_pack"

@dataclass
class ProblemFrame:
    workspace: str
    agent: str
    part: str
    process: str
    material: str
    quantities: List[str]
    concepts: List[str]
    missing_inputs: List[str]
    confidence: str

@dataclass
class RiskItem:
    area: str
    risk: str
    reason: str
    required_data: str
    recommended_action: str

@dataclass
class CalculationResult:
    name: str
    status: str
    details: str
    values: Dict[str, Any]

# -----------------------------------------------------------------------------
# Knowledge seeding and loading
# -----------------------------------------------------------------------------

def slugify(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]+", "_", text.strip()).strip("_") or "item"


def seed_deep_knowledge(force: bool = False) -> None:
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    for workspace, files in KNOWLEDGE_SEED.items():
        folder = KNOWLEDGE_DIR / workspace
        folder.mkdir(parents=True, exist_ok=True)
        for filename, content in files.items():
            path = folder / filename
            if force or not path.exists():
                path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
        notes = folder / "notes.md"
        if force or not notes.exists():
            notes.write_text(
                f"# {workspace.replace('_', ' ').title()} Knowledge Pack\n\n"
                "This workspace contains structured internal engineering reference notes. "
                "Use it as guidance, not as certified calculation or standards compliance.\n",
                encoding="utf-8",
            )


def strip_markdown(text: str) -> str:
    text = re.sub(r"`{1,3}", "", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    return text.strip()


def split_markdown_sections(text: str) -> List[Tuple[str, str]]:
    lines = text.splitlines()
    sections: List[Tuple[str, List[str]]] = []
    current_title = "Overview"
    current: List[str] = []
    for line in lines:
        if line.startswith("#"):
            if current:
                sections.append((strip_markdown(current_title), current))
            current_title = strip_markdown(line)
            current = []
        else:
            current.append(line)
    if current or not sections:
        sections.append((strip_markdown(current_title), current))
    out: List[Tuple[str, str]] = []
    for title, body in sections:
        body_text = strip_markdown("\n".join(body))
        if body_text:
            out.append((title, body_text))
    return out


def tokenize(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9+\-/%\.]+", " ", text)
    tokens = [t for t in text.split() if len(t) > 1]
    stop = {
        "the", "and", "for", "with", "from", "this", "that", "into", "using", "used", "use", "are", "was",
        "what", "how", "why", "can", "you", "your", "about", "create", "review", "plan", "setup", "design",
    }
    return [t for t in tokens if t not in stop]


QUERY_EXPANSIONS = {
    "mold": ["injection", "molding", "draft", "wall", "rib", "boss", "sink", "warpage", "shrinkage"],
    "molded": ["injection", "molding", "draft", "wall", "rib", "boss", "sink", "warpage", "shrinkage"],
    "plastic": ["thermoplastic", "abs", "pp", "pc", "nylon", "shrinkage", "wall"],
    "cover": ["enclosure", "cosmetic", "snap", "boss", "rib"],
    "bracket": ["fea", "static", "load", "constraint", "mesh", "stress"],
    "ansys": ["fea", "static", "mesh", "apdl", "constraint", "contact"],
    "fluent": ["cfd", "turbulence", "reynolds", "mesh", "y+", "boundary"],
    "pipe": ["internal", "flow", "reynolds", "pressure", "drop"],
    "solidworks": ["cad", "macro", "vba", "export", "step", "dxf"],
    "macro": ["vba", "solidworks", "export", "validation"],
    "shaft": ["torsion", "fatigue", "bearing", "keyway"],
    "bearing": ["l10", "radial", "axial", "life"],
}


def expanded_query_tokens(query: str) -> List[str]:
    base = tokenize(query)
    expanded = list(base)
    for t in base:
        expanded.extend(QUERY_EXPANSIONS.get(t, []))
    return expanded


def workspace_folder(workspace_name: str) -> Optional[str]:
    return WORKSPACES.get(workspace_name, {}).get("folder")


def load_knowledge_chunks(project: str = "RD_Lab") -> List[SourceChunk]:
    seed_deep_knowledge(force=False)
    chunks: List[SourceChunk] = []
    for folder in KNOWLEDGE_DIR.iterdir():
        if not folder.is_dir():
            continue
        for file in folder.glob("*.md"):
            try:
                text = file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for title, body in split_markdown_sections(text):
                if len(body.strip()) < 40:
                    continue
                chunks.append(SourceChunk(folder.name, str(file.relative_to(ROOT)), title, body, 0.0, "knowledge_pack"))
    # Project uploaded references, if any.
    ref_dir = PROJECT_MEMORY_DIR / slugify(project) / "references_text"
    if ref_dir.exists():
        for file in ref_dir.glob("*.txt"):
            try:
                text = file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for i, part in enumerate(chunk_text(text, 1200, 120)):
                chunks.append(SourceChunk("project_reference", str(file.relative_to(ROOT)), f"Uploaded reference chunk {i+1}", part, 0.0, "uploaded_reference"))
    return chunks


def chunk_text(text: str, size: int = 1400, overlap: int = 180) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= size:
        return [text] if text else []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def retrieve(query: str, workspace_name: str, project: str = "RD_Lab", top_k: int = 6) -> List[SourceChunk]:
    tokens = expanded_query_tokens(query)
    if not tokens:
        tokens = ["engineering"]
    token_counts = Counter(tokens)
    wanted_folder = workspace_folder(workspace_name)
    routed_folder = route_workspace(query, workspace_name)[1]
    chunks = load_knowledge_chunks(project)
    scored: List[SourceChunk] = []
    for ch in chunks:
        text = f"{ch.workspace} {ch.title} {ch.text}".lower()
        score = 0.0
        for tok, count in token_counts.items():
            if tok in text:
                score += 1.0 * count
                if tok in ch.title.lower():
                    score += 1.5
                if tok in ch.source.lower():
                    score += 0.8
        if wanted_folder and ch.workspace == wanted_folder:
            score *= 1.35
        if routed_folder and ch.workspace == routed_folder:
            score *= 1.75
        if ch.source_type == "uploaded_reference":
            score *= 1.25
        if score > 0:
            scored.append(SourceChunk(ch.workspace, ch.source, ch.title, ch.text, round(score, 3), ch.source_type))
    scored.sort(key=lambda x: x.score, reverse=True)
    # Diversify by source file.
    out: List[SourceChunk] = []
    seen = set()
    for item in scored:
        key = item.source
        if key not in seen:
            out.append(item)
            seen.add(key)
        if len(out) >= top_k:
            break
    return out

# -----------------------------------------------------------------------------
# Routing, ontology, reasoning
# -----------------------------------------------------------------------------

ROUTE_KEYWORDS = [
    ("CAD / SolidWorks", ["solidworks", "macro", "vba", "dxf", "step", "drawing", "bom", "cad"]),
    ("Simulation / FEA", ["fea", "ansys", "static structural", "modal", "buckling", "mesh", "stress", "constraint", "bracket"]),
    ("CFD / Thermal", ["cfd", "fluent", "flow", "reynolds", "pressure drop", "thermal", "heat", "y+", "turbulence"]),
    ("Manufacturing / DFM", ["dfm", "dfa", "manufacturing", "injection", "molding", "molded", "sheet metal", "machining", "tooling", "tolerance", "assembly"]),
    ("Materials Selection", ["material", "materials", "abs", "polypropylene", "nylon", "steel", "aluminum", "corrosion", "temperature"]),
    ("Innovation / Patent", ["patent", "claim", "novel", "invention", "prior art", "triz", "prototype"]),
    ("Product R&D / Design", ["shaft", "beam", "bearing", "gear", "spring", "fastener", "fatigue", "gd&t", "design"]),
]


def route_workspace(query: str, selected_workspace: str) -> Tuple[str, Optional[str]]:
    q = query.lower()
    scores: Dict[str, int] = defaultdict(int)
    for ws, keywords in ROUTE_KEYWORDS:
        for kw in keywords:
            if kw in q:
                scores[ws] += 1 if " " not in kw else 2
    if scores:
        best = max(scores, key=scores.get)
        return best, workspace_folder(best)
    return selected_workspace, workspace_folder(selected_workspace)


def detect_problem_frame(query: str, selected_workspace: str) -> ProblemFrame:
    routed_ws, _ = route_workspace(query, selected_workspace)
    q = query.lower()
    part = "not specified"
    for name, kws in {
        "cover/enclosure": ["cover", "enclosure", "lid", "housing"],
        "bracket": ["bracket", "mount"],
        "shaft": ["shaft"],
        "beam": ["beam"],
        "pipe/channel": ["pipe", "channel", "duct"],
        "gear": ["gear"],
        "spring": ["spring"],
        "bearing": ["bearing"],
    }.items():
        if any(k in q for k in kws):
            part = name
            break
    process = "not specified"
    for name, kws in {
        "injection molding": ["injection", "molded", "molding", "plastic cover"],
        "sheet metal forming": ["sheet metal", "bend", "flange"],
        "machining": ["machining", "cnc", "milling", "turning"],
        "static structural simulation": ["static", "fea", "ansys", "stress"],
        "internal fluid flow": ["pipe", "internal flow", "pressure drop"],
        "cad automation": ["solidworks", "macro", "vba", "dxf", "step"],
    }.items():
        if any(k in q for k in kws):
            process = name
            break
    material = "not specified"
    materials = ["abs", "pp", "polypropylene", "pc", "polycarbonate", "pa", "nylon", "steel", "aluminum", "stainless", "peek", "pom"]
    found_materials = [m.upper() if len(m) <= 4 else m for m in materials if m in q]
    if found_materials:
        material = ", ".join(sorted(set(found_materials)))
    quantities = re.findall(r"\b\d+(?:\.\d+)?\s*(?:kn|n|nm|n\*m|mm|cm|m|mpa|gpa|rpm|m/s|kg|pa|bar|deg|°c|c)\b", q)
    concepts = []
    for concept in [
        "function", "material family", "wall thickness", "draft", "ribs", "bosses", "shrinkage", "sink marks", "warpage", "parting line",
        "loads", "constraints", "mesh", "contacts", "convergence", "validation", "reynolds", "pressure drop", "turbulence", "y+",
        "tolerance", "assembly", "cost", "quality", "macro", "export", "drawing", "bom",
    ]:
        if concept in q or (concept == "wall thickness" and "wall" in q):
            concepts.append(concept)
    missing = missing_inputs_for(routed_ws, part, process, material, quantities, q)
    confidence = confidence_level(missing, quantities, material, process)
    return ProblemFrame(routed_ws, WORKSPACES[routed_ws]["agent"], part, process, material, quantities, concepts[:12], missing, confidence)


def missing_inputs_for(workspace: str, part: str, process: str, material: str, quantities: List[str], q: str) -> List[str]:
    base: List[str] = []
    if workspace == "Manufacturing / DFM":
        base = ["CAD image/STEP", "material grade", "nominal wall thickness", "production volume", "critical tolerances", "surface/cosmetic class", "assembly method"]
        if "injection" in process:
            base.extend(["rib and boss geometry", "draft target", "gate/ejector constraints", "parting line preference"])
    elif workspace == "Simulation / FEA":
        base = ["CAD geometry", "material model", "loads", "constraints", "contacts", "mesh strategy", "acceptance criteria", "validation method"]
    elif workspace == "CFD / Thermal":
        base = ["fluid properties", "domain geometry", "velocity/flow rate", "boundary conditions", "mesh/y+ target", "convergence criteria", "validation method"]
    elif workspace == "Materials Selection":
        base = ["function", "loads", "temperature", "environment/chemical exposure", "process", "cost target", "availability" ]
    elif workspace == "CAD / SolidWorks":
        base = ["SolidWorks version", "document type", "input folder", "output folder", "file naming convention", "overwrite policy", "backup policy"]
    elif workspace == "Product R&D / Design":
        base = ["function", "loads", "constraints", "material", "safety factor", "manufacturing process", "validation plan"]
    elif workspace == "Innovation / Patent":
        base = ["problem statement", "closest alternatives", "novel mechanism", "prototype evidence", "target market", "prior-art keywords"]
    else:
        base = ["objective", "function", "loads", "material", "geometry", "process", "validation criteria"]
    present = set()
    if material != "not specified":
        present.add("material grade")
        present.add("material")
    if quantities:
        for name in ["loads", "nominal wall thickness", "velocity/flow rate", "production volume"]:
            present.add(name)
    if any(w in q for w in ["step", "cad", "image", "drawing"]):
        present.add("CAD image/STEP")
        present.add("CAD geometry")
        present.add("geometry")
    return [x for x in base if x not in present][:12]


def confidence_level(missing: List[str], quantities: List[str], material: str, process: str) -> str:
    score = 100
    score -= min(60, len(missing) * 7)
    if not quantities:
        score -= 12
    if material == "not specified":
        score -= 10
    if process == "not specified":
        score -= 8
    if score >= 75:
        return "High"
    if score >= 50:
        return "Medium"
    if score >= 30:
        return "Low-to-medium"
    return "Low"


REASONING_PROTOCOLS = {
    "Manufacturing / DFM": [
        "Identify process family, material family, production volume, and surface/function requirements.",
        "Map geometry to process capability, tooling, cycle time, and defect modes.",
        "Score risks for wall thickness, draft, ribs/bosses, tooling, tolerance, assembly, quality, and cost.",
        "Rank corrective actions by risk reduction, cost impact, and ease of implementation.",
    ],
    "CAD / SolidWorks": [
        "Clarify document type, units, target geometry, output files, naming, and overwrite policy.",
        "Separate geometry creation, feature creation, drawing, BOM, export, and validation.",
        "Generate clean macro structure with error handling and user-visible run instructions.",
        "Validate destructive operations and file paths before execution.",
    ],
    "Simulation / FEA": [
        "Define simulation objective, physics, acceptance criterion, and decision supported.",
        "Check loads, constraints, contacts, material model, element type, mesh, and convergence.",
        "Plan validation using hand calculation, benchmark, or test evidence.",
        "Interpret plots only after assumptions, boundary conditions, and convergence are verified.",
    ],
    "CFD / Thermal": [
        "Define domain, flow regime, fluid properties, boundary conditions, and heat sources.",
        "Check Reynolds number, turbulence model, mesh/y+, convergence, and conservation balances.",
        "Validate using analytical pressure drop/heat transfer estimates or test data.",
    ],
    "Materials Selection": [
        "Translate function into constraints, objectives, and free variables.",
        "Screen materials by temperature, load, environment, process, cost, and availability.",
        "Rank candidates and validate with supplier datasheets and tests.",
    ],
    "Product R&D / Design": [
        "Clarify function, loads, constraints, materials, failure modes, manufacturing process, and validation.",
        "Perform sanity calculations before detailed CAD/FEA.",
        "Rank design risks and define next experiments/tests.",
    ],
    "Innovation / Patent": [
        "Separate novelty, usefulness, feasibility, manufacturability, and commercial value.",
        "Map prior-art search terms and closest alternatives.",
        "Convert concept into testable prototype requirements and claim hypotheses.",
    ],
    "General engineering": [
        "Classify engineering domain and objective.",
        "Extract known inputs and missing data.",
        "Retrieve internal sources and apply the nearest workspace protocol.",
    ],
}

# -----------------------------------------------------------------------------
# Risk and scoring engines
# -----------------------------------------------------------------------------

RISK_ORDER = {"Low": 1, "Medium": 2, "High": 3, "Unknown": 2}


def build_risk_matrix(frame: ProblemFrame, query: str) -> List[RiskItem]:
    ws = frame.workspace
    missing = set(frame.missing_inputs)
    risks: List[RiskItem] = []
    if ws == "Manufacturing / DFM":
        risks = [
            RiskItem("Wall thickness", "High" if "nominal wall thickness" in missing else "Medium", "Injection molding requires uniform wall and no nominal thickness was confirmed.", "Nominal wall thickness, material grade", "Keep wall uniform; avoid abrupt thick sections; validate sink/warpage."),
            RiskItem("Draft", "Medium" if "draft target" in missing else "Low", "Mold release needs draft on vertical walls, ribs and bosses.", "Draft target and cosmetic faces", "Add draft early and align parting direction with tooling strategy."),
            RiskItem("Ribs / bosses", "High" if "rib and boss geometry" in missing else "Medium", "Covers often use bosses/ribs; thick bosses can create sink and cycle-time penalties.", "Rib thickness, boss OD/ID, screw loads", "Use ribs for stiffness; core bosses; avoid thick intersections."),
            RiskItem("Tooling / parting", "Medium" if "parting line preference" in missing else "Low", "Parting line, gates, and ejectors control appearance and manufacturing stability.", "Gate/ejector constraints, parting preference", "Define cosmetic surfaces and gate/ejector zones before tooling."),
            RiskItem("Tolerance capability", "Unknown" if "critical tolerances" in missing else "Medium", "No critical dimensions or process capability were defined.", "CTQ dimensions and tolerances", "Link tolerances to function and process capability."),
            RiskItem("Assembly / DFA", "Unknown" if "assembly method" in missing else "Medium", "Mating parts, fasteners and snap-fits are unknown.", "Assembly method and mating geometry", "Review snap-fit, screw bosses, access and serviceability."),
            RiskItem("Quality plan", "Medium", "Sink, warpage, flash and dimensional variation are likely control points.", "Inspection method and CTQs", "Define CTQ dimensions and first-article inspection plan."),
        ]
    elif ws == "Simulation / FEA":
        risks = [
            RiskItem("Objective", "Medium" if "acceptance criteria" in missing else "Low", "Simulation purpose and acceptance criteria must be explicit.", "Decision supported and pass/fail criteria", "Define what engineering decision this FEA supports."),
            RiskItem("Loads", "High" if "loads" in missing else "Medium", "Loads drive stress/deflection; missing or idealized loads reduce credibility.", "Load magnitude, direction, distribution", "Document load case and compare with hand estimate."),
            RiskItem("Constraints", "High" if "constraints" in missing else "Medium", "Boundary conditions often dominate FEA results.", "Support/contact constraints", "Use physically realistic constraints and sensitivity checks."),
            RiskItem("Mesh convergence", "High" if "mesh strategy" in missing else "Medium", "Unconverged stress results are not release-ready.", "Element type and convergence plan", "Run mesh refinement for quantity of interest."),
            RiskItem("Validation", "High" if "validation method" in missing else "Medium", "Simulation must be validated against hand/test/benchmark evidence.", "Validation method", "Plan hand calculation or test correlation."),
        ]
    elif ws == "CFD / Thermal":
        risks = [
            RiskItem("Flow regime", "High" if "fluid properties" in missing or "velocity/flow rate" in missing else "Medium", "Reynolds number cannot be classified without fluid and velocity data.", "Fluid, density, viscosity, velocity, length", "Compute Reynolds number before model choice."),
            RiskItem("Boundary conditions", "High" if "boundary conditions" in missing else "Medium", "CFD results are highly boundary-condition sensitive.", "Inlets/outlets/walls/thermal BCs", "Define physical boundary conditions and conservation checks."),
            RiskItem("Mesh/y+", "High" if "mesh/y+ target" in missing else "Medium", "Wall treatment must match turbulence model and mesh.", "y+ target, inflation layers", "Check y+ after solution and refine mesh."),
            RiskItem("Validation", "High" if "validation method" in missing else "Medium", "CFD requires analytical or experimental sanity checks.", "Pressure/temperature/flow validation", "Compare with correlations or test data."),
        ]
    elif ws == "Materials Selection":
        risks = [
            RiskItem("Functional constraints", "High" if "function" in missing else "Medium", "Material choice cannot be made without function and constraints.", "Function, load, environment", "Define hard constraints before ranking materials."),
            RiskItem("Thermal/environment", "Medium" if "temperature" in missing else "Low", "Temperature and chemicals can invalidate material choice.", "Temperature and exposure", "Screen materials by temperature and environment."),
            RiskItem("Process compatibility", "High" if "process" in missing else "Medium", "Material must match manufacturing process.", "Process and volume", "Filter candidates by process and supplier availability."),
        ]
    elif ws == "CAD / SolidWorks":
        risks = [
            RiskItem("Overwrite/file safety", "High" if "overwrite policy" in missing else "Medium", "Automation can overwrite files if policy is unclear.", "Output folder and overwrite policy", "Default to non-destructive export and logs."),
            RiskItem("Document validation", "Medium" if "document type" in missing else "Low", "Macro behavior depends on part/assembly/drawing type.", "Document type", "Validate active document before running."),
            RiskItem("Path/naming", "Medium" if "file naming convention" in missing else "Low", "Export workflows need deterministic names and paths.", "Naming convention and output folder", "Use safe filenames and user-selected folder."),
        ]
    else:
        risks = [
            RiskItem("Problem definition", "Medium", "The engineering objective is not fully specified.", "Objective, constraints, inputs", "Clarify objective and required decision."),
            RiskItem("Validation", "High", "No validation method has been defined.", "Test/calculation/inspection evidence", "Define validation before release."),
        ]
    return risks


def risk_score(risks: List[RiskItem], frame: ProblemFrame) -> Tuple[int, str]:
    if not risks:
        return 50, "Unknown"
    penalty = 0
    for r in risks:
        penalty += {"High": 12, "Medium": 7, "Low": 3, "Unknown": 9}.get(r.risk, 6)
    penalty += min(20, len(frame.missing_inputs) * 2)
    score = max(5, min(95, 100 - penalty))
    if score >= 80:
        level = "Low risk / strong readiness"
    elif score >= 65:
        level = "Medium risk"
    elif score >= 45:
        level = "Medium-high risk"
    else:
        level = "High risk / low readiness"
    return score, level


def workspace_score_name(ws: str) -> str:
    return {
        "Manufacturing / DFM": "DFM Score",
        "CAD / SolidWorks": "CAD Automation Readiness Score",
        "Simulation / FEA": "FEA Setup Quality Score",
        "CFD / Thermal": "CFD Setup Quality Score",
        "Materials Selection": "Material Suitability Readiness Score",
        "Innovation / Patent": "Patent Novelty Readiness Score",
        "Product R&D / Design": "Mechanical Design Readiness Score",
    }.get(ws, "Engineering Readiness Score")

# -----------------------------------------------------------------------------
# Engineering calculators and validators
# -----------------------------------------------------------------------------

def find_value(query: str, patterns: List[str]) -> Optional[float]:
    q = query.lower().replace("×", "x")
    for pat in patterns:
        m = re.search(pat, q)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                pass
    return None


def engineering_calculators(query: str, frame: ProblemFrame) -> List[CalculationResult]:
    q = query.lower()
    results: List[CalculationResult] = []
    # Beam check
    if any(k in q for k in ["beam", "deflection", "bending"]):
        P = find_value(q, [r"(?:load|p)\s*=\s*(\d+(?:\.\d+)?)\s*n", r"(\d+(?:\.\d+)?)\s*n\s*(?:load)?"])
        Lmm = find_value(q, [r"(?:span|length|l)\s*=\s*(\d+(?:\.\d+)?)\s*mm", r"(\d+(?:\.\d+)?)\s*mm\s*(?:span|long|length)"])
        EGPa = find_value(q, [r"(?:e|modulus)\s*=\s*(\d+(?:\.\d+)?)\s*gpa"])
        Imm4 = find_value(q, [r"(?:i)\s*=\s*(\d+(?:\.\d+)?)\s*mm", r"i\s*=\s*(\d+(?:\.\d+)?)"])
        if P and Lmm and EGPa and Imm4:
            delta = P * (Lmm**3) / (48 * (EGPa * 1000) * Imm4)
            results.append(CalculationResult("Beam center-load deflection", "computed", f"Simply supported estimate: delta = {delta:.3f} mm using P L^3/(48 E I).", {"P_N": P, "L_mm": Lmm, "E_GPa": EGPa, "I_mm4": Imm4, "delta_mm": delta}))
        else:
            results.append(CalculationResult("Beam bending/deflection", "missing inputs", "Provide load P [N], span L [mm], E [GPa], and I [mm^4] for deterministic beam check.", {}))
    # Shaft torsion
    if "shaft" in q or "torsion" in q:
        T = find_value(q, [r"(?:torque|t)\s*=\s*(\d+(?:\.\d+)?)\s*(?:n\s*m|nm)", r"(\d+(?:\.\d+)?)\s*(?:n\s*m|nm)"])
        dmm = find_value(q, [r"(?:diameter|d)\s*=\s*(\d+(?:\.\d+)?)\s*mm", r"(\d+(?:\.\d+)?)\s*mm\s*(?:diameter|dia)"])
        if T and dmm:
            tau = 16 * (T * 1000) / (math.pi * dmm**3)
            results.append(CalculationResult("Solid shaft torsion", "computed", f"tau_max = {tau:.2f} MPa using 16T/(pi d^3).", {"T_Nm": T, "d_mm": dmm, "tau_MPa": tau}))
        else:
            results.append(CalculationResult("Shaft torsion", "missing inputs", "Provide torque [N·m] and shaft diameter [mm] for torsional stress check.", {}))
    # Reynolds
    if any(k in q for k in ["reynolds", "pipe", "flow", "pressure drop", "cfd"]):
        rho = find_value(q, [r"rho\s*=\s*(\d+(?:\.\d+)?)", r"density\s*=\s*(\d+(?:\.\d+)?)"])
        V = find_value(q, [r"(?:velocity|v)\s*=\s*(\d+(?:\.\d+)?)\s*m/s", r"(\d+(?:\.\d+)?)\s*m/s"])
        Dmm = find_value(q, [r"(?:diameter|d)\s*=\s*(\d+(?:\.\d+)?)\s*mm", r"(\d+(?:\.\d+)?)\s*mm\s*(?:pipe|diameter|dia)"])
        mu = find_value(q, [r"(?:mu|viscosity)\s*=\s*(\d+(?:\.\d+)?)"])
        if V and Dmm:
            rho = rho or 998.0
            mu = mu or 0.001
            Re = rho * V * (Dmm / 1000) / mu
            regime = "laminar" if Re < 2300 else "transitional" if Re < 4000 else "turbulent"
            results.append(CalculationResult("Reynolds number", "computed", f"Re ≈ {Re:,.0f}; regime: {regime}. Defaults used if fluid data missing: water near room temperature.", {"rho": rho, "V_mps": V, "D_mm": Dmm, "mu_Pa_s": mu, "Re": Re, "regime": regime}))
        else:
            results.append(CalculationResult("Reynolds number", "missing inputs", "Provide velocity [m/s] and diameter [mm]; density and viscosity optional but recommended.", {}))
    # Sheet metal bend
    if "sheet" in q or "bend" in q:
        t = find_value(q, [r"(?:thickness|t)\s*=\s*(\d+(?:\.\d+)?)\s*mm"])
        R = find_value(q, [r"(?:radius|r)\s*=\s*(\d+(?:\.\d+)?)\s*mm"])
        A = find_value(q, [r"(?:angle|a)\s*=\s*(\d+(?:\.\d+)?)"])
        K = find_value(q, [r"(?:k)\s*=\s*(\d+(?:\.\d+)?)"])
        if t and R and A:
            K = K or 0.33
            BA = math.radians(A) * (R + K * t)
            results.append(CalculationResult("Sheet metal bend allowance", "computed", f"Bend allowance ≈ {BA:.2f} mm using BA = angle_rad*(R+K*t).", {"t_mm": t, "R_mm": R, "angle_deg": A, "K": K, "BA_mm": BA}))
        else:
            results.append(CalculationResult("Sheet metal bend allowance", "missing inputs", "Provide thickness, inside radius, bend angle, and optional K-factor.", {}))
    # Bearing L10
    if "bearing" in q or "l10" in q:
        C = find_value(q, [r"(?:c)\s*=\s*(\d+(?:\.\d+)?)\s*n", r"dynamic rating\s*=\s*(\d+(?:\.\d+)?)"])
        P = find_value(q, [r"(?:equivalent load|p)\s*=\s*(\d+(?:\.\d+)?)\s*n"])
        rpm = find_value(q, [r"(?:rpm|speed)\s*=\s*(\d+(?:\.\d+)?)"])
        if C and P and rpm:
            L10_mrev = (C / P) ** 3
            L10_h = L10_mrev * 1e6 / (60 * rpm)
            results.append(CalculationResult("Bearing L10 life", "computed", f"Ball bearing estimate: L10 ≈ {L10_mrev:.2f} million rev, {L10_h:.1f} hours.", {"C_N": C, "P_N": P, "rpm": rpm, "L10_mrev": L10_mrev, "L10_hours": L10_h}))
        else:
            results.append(CalculationResult("Bearing L10 life", "missing inputs", "Provide dynamic rating C [N], equivalent load P [N], and speed [rpm].", {}))
    # Injection molding wall/rib quick check
    if any(k in q for k in ["injection", "mold", "molded", "plastic"]):
        wall = find_value(q, [r"(?:wall|thickness)\s*=\s*(\d+(?:\.\d+)?)\s*mm", r"(\d+(?:\.\d+)?)\s*mm\s*wall"])
        rib = find_value(q, [r"(?:rib)\s*=\s*(\d+(?:\.\d+)?)\s*mm", r"rib\s*thickness\s*(?:is|=)?\s*(\d+(?:\.\d+)?)"])
        if wall:
            msg = f"Nominal wall thickness provided: {wall:.2f} mm. Check uniformity, sink, flow length, material-specific recommendations, and tolerance stability."
            values = {"wall_mm": wall}
            if rib:
                ratio = rib / wall
                risk = "higher sink risk" if ratio > 0.65 else "typical preliminary rib ratio"
                msg += f" Rib/wall ratio = {ratio:.2f}; {risk}."
                values["rib_mm"] = rib
                values["rib_wall_ratio"] = ratio
            results.append(CalculationResult("Injection molding wall/rib sanity check", "computed", msg, values))
        else:
            results.append(CalculationResult("Injection molding wall/rib check", "missing inputs", "Provide nominal wall thickness and rib/boss dimensions for deterministic molding DFM checks.", {}))
    return results

# -----------------------------------------------------------------------------
# CAD / Simulation artifact builders
# -----------------------------------------------------------------------------

def generate_solidworks_macro(task: str) -> str:
    return f"""' MechAI Pro generated SolidWorks VBA macro skeleton
' Task: {task}
' Safety: Review all paths and backup files before running.
Option Explicit

Dim swApp As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim errors As Long
Dim warnings As Long

Sub main()
    On Error GoTo EH
    Set swApp = Application.SldWorks
    Set swModel = swApp.ActiveDoc
    
    If swModel Is Nothing Then
        MsgBox "No active SolidWorks document found.", vbExclamation
        Exit Sub
    End If
    
    Dim docPath As String
    docPath = swModel.GetPathName
    If docPath = "" Then
        MsgBox "Please save the document before export.", vbExclamation
        Exit Sub
    End If
    
    Dim folder As String
    folder = Left(docPath, InStrRev(docPath, "\\"))
    
    Dim baseName As String
    baseName = Mid(docPath, InStrRev(docPath, "\\") + 1)
    baseName = Left(baseName, InStrRev(baseName, ".") - 1)
    
    ' Export STEP
    swModel.Extension.SaveAs folder & baseName & ".STEP", 0, 0, Nothing, errors, warnings
    
    ' Export DXF placeholder: for sheet-metal flat patterns, replace with flat pattern export API.
    ' swModel.Extension.SaveAs folder & baseName & ".DXF", 0, 0, Nothing, errors, warnings
    
    MsgBox "Export routine completed. Check output folder and warnings.", vbInformation
    Exit Sub
EH:
    MsgBox "Macro failed: " & Err.Description, vbCritical
End Sub
"""


def validate_macro(macro: str) -> List[str]:
    checks = []
    checks.append("PASS: Contains Option Explicit." if "Option Explicit" in macro else "FAIL: Missing Option Explicit.")
    checks.append("PASS: Has error handler." if "On Error" in macro and "EH:" in macro else "FAIL: Missing error handler.")
    checks.append("PASS: Checks active document." if "ActiveDoc" in macro and "Nothing" in macro else "FAIL: Active document validation not obvious.")
    checks.append("PASS: Mentions backup/review safety." if "backup" in macro.lower() or "review" in macro.lower() else "WARN: Add backup warning.")
    return checks


def generate_apdl_plan(query: str) -> str:
    return f"""! MechAI Pro ANSYS APDL starter skeleton
! User request: {query}
! Review geometry, material, loads, constraints, units and validation before use.
/PREP7
! TODO: Define element type
ET,1,SOLID186
! TODO: Define material properties
MP,EX,1,210000
MP,PRXY,1,0.3
! TODO: Import/build geometry and mesh
! TODO: Apply boundary conditions and loads
/SOLU
ANTYPE,0
SOLVE
/POST1
! TODO: Review displacement, stress, reactions, convergence, and validation checks
"""


def generate_fluent_journal(query: str) -> str:
    return f"""; MechAI Pro Fluent journal starter
; User request: {query}
; Review mesh, units, boundary conditions, turbulence model, y+, convergence and validation.
/file/read-case-data case.cas.h5
/solve/initialize/hyb-initialization
; TODO: set models, materials, boundary conditions
; TODO: iterate and monitor residuals + mass/energy balances
/solve/iterate 500
/file/write-case-data result.cas.h5
"""

# -----------------------------------------------------------------------------
# Project memory and references
# -----------------------------------------------------------------------------

def project_dir(project: str) -> Path:
    d = PROJECT_MEMORY_DIR / slugify(project)
    d.mkdir(parents=True, exist_ok=True)
    (d / "uploads").mkdir(exist_ok=True)
    (d / "references_text").mkdir(exist_ok=True)
    (d / "reports").mkdir(exist_ok=True)
    (d / "artifacts").mkdir(exist_ok=True)
    return d


def memory_path(project: str) -> Path:
    return project_dir(project) / "project_memory.json"


def default_memory(project: str) -> Dict[str, Any]:
    return {
        "project": project,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "questions": [],
        "decisions": [],
        "assumptions": [],
        "materials": [],
        "calculations": [],
        "uploaded_files": [],
        "generated_reports": [],
        "lessons_learned": [],
        "risks": [],
    }


def load_memory(project: str) -> Dict[str, Any]:
    path = memory_path(project)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default_memory(project)
    return default_memory(project)


def save_memory(project: str, memory: Dict[str, Any]) -> None:
    memory["updated_at"] = datetime.now().isoformat(timespec="seconds")
    memory_path(project).write_text(json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8")


def append_memory(project: str, question: str, answer: str, frame: ProblemFrame, risks: List[RiskItem], calcs: List[CalculationResult], sources: List[SourceChunk]) -> None:
    mem = load_memory(project)
    mem["questions"].append({"time": datetime.now().isoformat(timespec="seconds"), "question": question, "workspace": frame.workspace})
    mem["assumptions"].append({"time": datetime.now().isoformat(timespec="seconds"), "items": frame.missing_inputs[:6], "confidence": frame.confidence})
    mem["risks"].append({"time": datetime.now().isoformat(timespec="seconds"), "workspace": frame.workspace, "risks": [asdict(r) for r in risks]})
    if calcs:
        mem["calculations"].append({"time": datetime.now().isoformat(timespec="seconds"), "items": [asdict(c) for c in calcs]})
    mem["decisions"].append({
        "time": datetime.now().isoformat(timespec="seconds"),
        "summary": f"Applied {frame.workspace} reasoning; confidence {frame.confidence}; sources {len(sources)}.",
        "sources": [s.source for s in sources[:5]],
    })
    save_memory(project, mem)


def extract_uploaded_text(file) -> Tuple[str, str]:
    name = file.name
    suffix = Path(name).suffix.lower()
    data = file.getvalue()
    if suffix == ".pdf":
        if PyPDF2 is None:
            return "", "PyPDF2 is not installed; cannot extract PDF text."
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(data))
            text = []
            for page in reader.pages[:80]:
                text.append(page.extract_text() or "")
            return "\n".join(text).strip(), "ok"
        except Exception as e:
            return "", f"PDF extraction failed: {e}"
    if suffix in [".txt", ".md", ".csv"]:
        try:
            return data.decode("utf-8", errors="ignore"), "ok"
        except Exception as e:
            return "", f"Text extraction failed: {e}"
    return "", "Unsupported file type for text ingestion."


def ingest_reference(project: str, workspace_name: str, uploaded_file, source_type: str, legal_note: str) -> str:
    pdir = project_dir(project)
    safe_name = slugify(Path(uploaded_file.name).stem) + Path(uploaded_file.name).suffix.lower()
    raw_path = pdir / "uploads" / safe_name
    raw_path.write_bytes(uploaded_file.getvalue())
    text, status = extract_uploaded_text(uploaded_file)
    registry_path = pdir / "source_registry.json"
    registry = []
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except Exception:
            registry = []
    entry = {
        "id": str(uuid.uuid4())[:8],
        "filename": uploaded_file.name,
        "stored_as": str(raw_path.relative_to(ROOT)),
        "workspace": workspace_name,
        "source_type": source_type,
        "legal_note": legal_note,
        "ingested_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "text_chars": len(text),
    }
    registry.append(entry)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    mem = load_memory(project)
    mem["uploaded_files"].append(entry)
    save_memory(project, mem)
    if text:
        txt_name = safe_name + ".txt"
        (pdir / "references_text" / txt_name).write_text(text, encoding="utf-8")
    return status

# -----------------------------------------------------------------------------
# Reports
# -----------------------------------------------------------------------------

def memory_to_markdown(project: str) -> str:
    mem = load_memory(project)
    lines = [f"# MechAI Pro Engineering Report — {project}", "", f"Generated: {datetime.now().isoformat(timespec='seconds')}", "", "## Project Memory Summary"]
    for key in ["questions", "decisions", "assumptions", "materials", "calculations", "uploaded_files", "risks", "lessons_learned"]:
        lines.append(f"\n### {key.replace('_', ' ').title()}")
        items = mem.get(key, [])
        if not items:
            lines.append("- No records yet.")
        else:
            for item in items[-10:]:
                lines.append("- " + json.dumps(item, ensure_ascii=False)[:1000])
    lines.append("\n## Engineering Use Note")
    lines.append("This report is generated from internal MechAI project memory. Validate calculations, standards compliance, CAD/FEA/CFD assumptions, and test evidence before engineering release.")
    return "\n".join(lines)


def make_docx_bytes(markdown_text: str) -> Optional[bytes]:
    if Document is None:
        return None
    doc = Document()
    for line in markdown_text.splitlines():
        if line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        elif line.startswith("### "):
            doc.add_heading(line[4:], level=3)
        elif line.startswith("- "):
            doc.add_paragraph(line[2:], style="List Bullet")
        else:
            doc.add_paragraph(line)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def make_pdf_bytes(markdown_text: str) -> Optional[bytes]:
    if canvas is None or A4 is None:
        return None
    bio = io.BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    width, height = A4
    x, y = 42, height - 48
    for raw in markdown_text.splitlines():
        line = strip_markdown(raw)
        if not line:
            y -= 10
            continue
        for wrapped in textwrap.wrap(line, width=95):
            c.drawString(x, y, wrapped[:120])
            y -= 14
            if y < 50:
                c.showPage()
                y = height - 48
        if raw.startswith("#"):
            y -= 8
    c.save()
    return bio.getvalue()


def make_xlsx_bytes(project: str) -> Optional[bytes]:
    if Workbook is None:
        return None
    mem = load_memory(project)
    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.append(["Category", "Count"])
    for key, val in mem.items():
        if isinstance(val, list):
            ws.append([key, len(val)])
    for key in ["questions", "decisions", "risks", "calculations", "uploaded_files"]:
        sheet = wb.create_sheet(key[:31])
        sheet.append(["JSON record"])
        for item in mem.get(key, [])[-100:]:
            sheet.append([json.dumps(item, ensure_ascii=False)])
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()

# -----------------------------------------------------------------------------
# Evaluation tests
# -----------------------------------------------------------------------------

EVAL_CASES = [
    {"q": "Create a DFM review for an injection molded plastic cover.", "must": ["Manufacturing", "wall", "draft", "risk", "missing"]},
    {"q": "Create an ANSYS static structural setup plan for a bracket loaded by 2 kN.", "must": ["FEA", "loads", "constraints", "mesh", "validation"]},
    {"q": "Calculate Reynolds number for water in a 20 mm pipe at 1 m/s.", "must": ["Reynolds", "regime"]},
    {"q": "Generate a SolidWorks macro skeleton to export STEP and DXF files.", "must": ["SolidWorks", "macro", "export", "validation"]},
]


def run_quality_tests() -> List[Dict[str, Any]]:
    results = []
    for case in EVAL_CASES:
        frame = detect_problem_frame(case["q"], "General engineering")
        sources = retrieve(case["q"], frame.workspace, "RD_Lab", 5)
        risks = build_risk_matrix(frame, case["q"])
        calcs = engineering_calculators(case["q"], frame)
        answer = build_answer(case["q"], frame, sources, risks, calcs, project="RD_Lab", for_test=True)
        text = answer.lower()
        passed_terms = [term for term in case["must"] if term.lower() in text]
        results.append({"question": case["q"], "workspace": frame.workspace, "passed": len(passed_terms), "required": len(case["must"]), "terms_found": passed_terms})
    return results

# -----------------------------------------------------------------------------
# Answer builder
# -----------------------------------------------------------------------------

def build_answer(query: str, frame: ProblemFrame, sources: List[SourceChunk], risks: List[RiskItem], calcs: List[CalculationResult], project: str, for_test: bool = False) -> str:
    score, level = risk_score(risks, frame)
    score_name = workspace_score_name(frame.workspace)
    protocol = REASONING_PROTOCOLS.get(frame.workspace, REASONING_PROTOCOLS["General engineering"])
    lines: List[str] = []
    lines.append(f"### Mechanical Decision Engine v25 — {frame.workspace}")
    lines.append("")
    lines.append("#### Problem frame")
    lines.append(f"- Part/component: **{frame.part}**.")
    lines.append(f"- Process/physics: **{frame.process}**.")
    lines.append(f"- Material: **{frame.material}**.")
    lines.append(f"- Quantities detected: **{', '.join(frame.quantities) if frame.quantities else 'not specified'}**.")
    lines.append(f"- Confidence: **{frame.confidence}**.")
    if frame.concepts:
        lines.append(f"- Key concepts considered: {', '.join(frame.concepts)}.")
    lines.append("")
    lines.append("#### Reasoning protocol applied")
    for i, item in enumerate(protocol, 1):
        lines.append(f"{i}. {item}")
    lines.append("")
    lines.append(f"#### {score_name}")
    lines.append(f"- Score: **{score}/100**")
    lines.append(f"- Risk/readiness level: **{level}**")
    lines.append("")
    lines.append("#### Risk matrix")
    lines.append("| Area | Risk | Reason | Required data | Recommended action |")
    lines.append("|---|---:|---|---|---|")
    for r in risks:
        lines.append(f"| {r.area} | {r.risk} | {r.reason} | {r.required_data} | {r.recommended_action} |")
    lines.append("")
    lines.append("#### Engineering calculators / deterministic validators")
    if calcs:
        for c in calcs:
            lines.append(f"- **{c.name}** — {c.status}: {c.details}")
    else:
        lines.append("- No deterministic calculation was possible from the current text. Provide numeric inputs to run calculators.")
    lines.append("")
    lines.append("#### Missing inputs before engineering release")
    if frame.missing_inputs:
        for item in frame.missing_inputs:
            lines.append(f"- {item}")
    else:
        lines.append("- No obvious critical missing inputs detected from this short prompt, but release validation is still required.")
    lines.append("")
    lines.append("#### Ranked recommendations")
    recs = ranked_recommendations(frame, risks)
    for i, rec in enumerate(recs, 1):
        lines.append(f"{i}. {rec}")
    lines.append("")
    lines.append("#### Internal retrieval and citations")
    if sources:
        for i, src in enumerate(sources[:6], 1):
            conf = "high" if src.score >= 12 else "medium" if src.score >= 6 else "low"
            lines.append(f"- [K{i}] **{src.workspace.replace('_', ' ').title()}** — `{src.source}` — relevance {src.score}, source confidence {conf}.")
    else:
        lines.append("- No matching internal source found. Add legal references or expand the relevant Knowledge Pack.")
    lines.append("")
    lines.append("#### Engineering use note")
    lines.append("This is internal guidance, not a certified calculation or standards release. Validate CAD geometry, material data, calculations, simulation assumptions, compliance, and physical test evidence before release.")
    return "\n".join(lines)


def ranked_recommendations(frame: ProblemFrame, risks: List[RiskItem]) -> List[str]:
    high = [r for r in risks if r.risk == "High"]
    medium = [r for r in risks if r.risk in ["Medium", "Unknown"]]
    recs = []
    for r in high[:3]:
        recs.append(f"Resolve **{r.area}** first: {r.recommended_action}")
    for r in medium[:3]:
        recs.append(f"Reduce **{r.area}** uncertainty: collect {r.required_data}.")
    if frame.workspace == "Manufacturing / DFM":
        recs.append("Upload CAD/STEP or provide wall thickness/material/volume to convert this from preliminary review to actionable DFM release review.")
    elif frame.workspace == "Simulation / FEA":
        recs.append("Define loads, constraints, material and validation target before treating simulation output as evidence.")
    elif frame.workspace == "CAD / SolidWorks":
        recs.append("Confirm document type, output folder and overwrite policy before running any macro.")
    return recs[:6]

# -----------------------------------------------------------------------------
# UI styling
# -----------------------------------------------------------------------------

st.set_page_config(page_title=APP_TITLE, page_icon="⚙️", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
<style>
:root { --bg:#000; --panel:#0f0f10; --panel2:#17181d; --text:#f4f4f5; --muted:#a1a1aa; --line:#2b2b2f; --accent:#ff4b4b; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background:#000 !important; color:var(--text) !important; }
[data-testid="stHeader"] { background:transparent !important; }
[data-testid="stToolbar"], #MainMenu, footer { visibility:hidden !important; display:none !important; }
section[data-testid="stSidebar"] { background:#050505 !important; border-right:1px solid #222 !important; min-width:292px !important; max-width:292px !important; width:292px !important; }
section[data-testid="stSidebar"] * { color:#f6f6f6 !important; }
.block-container { max-width:1060px !important; padding-top:3.0rem !important; padding-bottom:8rem !important; }
.stButton>button { background:#2d2d2d !important; border:0 !important; border-radius:12px !important; color:#fff !important; min-height:44px; }
.stDownloadButton>button { background:#242428 !important; border:1px solid #444 !important; border-radius:12px !important; color:#fff !important; }
[data-testid="stChatMessage"] { background:transparent !important; border:0 !important; }
[data-testid="stChatInput"] { background:#101114 !important; border-top:1px solid #222 !important; padding-left:31%; padding-right:4%; }
[data-testid="stChatInput"] textarea { background:#202020 !important; border:1px solid #3a3a3a !important; color:#fff !important; border-radius:28px !important; min-height:58px !important; }
.small-muted { color:#9ca3af; font-size:0.88rem; line-height:1.55; }
.sidebar-title { font-size:1.45rem; font-weight:800; margin: 1.2rem 0 1.4rem 0; }
.report-card { border:1px solid #242424; border-radius:14px; padding:1rem; background:#090909; }
code { color:#7ee787 !important; background:#111 !important; }
table { font-size:0.92rem; }
th, td { border-color:#333 !important; }
@media (max-width: 900px) {
    section[data-testid="stSidebar"] { min-width:260px !important; max-width:260px !important; width:260px !important; }
    [data-testid="stChatInput"] { padding-left:270px; padding-right:0.8rem; }
    .block-container { padding-left:1rem !important; padding-right:1rem !important; }
}
</style>
""",
    unsafe_allow_html=True,
)

# Ensure deep packs exist at runtime.
seed_deep_knowledge(force=False)

# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []
if "project" not in st.session_state:
    st.session_state.project = "RD_Lab"
if "workspace" not in st.session_state:
    st.session_state.workspace = "General engineering"

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------

with st.sidebar:
    st.markdown('<div class="sidebar-title">MechAI Pro</div>', unsafe_allow_html=True)
    if st.button("✎ New chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("⌕ Search chats")
    st.markdown("Ⅲ Library")
    st.markdown("### Workspace")
    ws_names = list(WORKSPACES.keys())
    st.session_state.workspace = st.selectbox(
        "Workspace", ws_names,
        index=ws_names.index(st.session_state.workspace) if st.session_state.workspace in ws_names else 0,
        label_visibility="collapsed",
        format_func=lambda x: f"{WORKSPACES[x]['icon']} {x}",
    )
    st.markdown('<div class="small-muted">Workspace biases the internal mechanical brain. Auto-routing still reads the question.</div>', unsafe_allow_html=True)
    st.markdown("### View")
    view = st.radio("View", ["Chat", "About"], horizontal=True, label_visibility="collapsed")
    st.markdown("### Projects")
    existing_projects = sorted([p.name for p in PROJECT_MEMORY_DIR.iterdir() if p.is_dir()]) or ["RD_Lab"]
    if "RD_Lab" not in existing_projects:
        existing_projects.insert(0, "RD_Lab")
    st.session_state.project = st.selectbox("Project", existing_projects, index=existing_projects.index(st.session_state.project) if st.session_state.project in existing_projects else 0, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("+ Project", use_container_width=True):
            new_name = f"Project_{datetime.now().strftime('%H%M%S')}"
            project_dir(new_name)
            st.session_state.project = new_name
            st.rerun()
    with c2:
        if st.button("Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    with st.expander("Reference Library / المراجع", expanded=False):
        st.markdown("Upload only legal/public/owned references. Avoid confidential files on public deployment.")
        source_type = st.selectbox("Source type", ["Open reference", "Company document", "Datasheet", "Catalog", "Design guide", "Standards summary", "Own engineering note"])
        legal_note = st.text_input("Legal/source note", value="User confirms rights to use this file for internal reference.")
        uploads = st.file_uploader("Upload references", type=["pdf", "txt", "md", "csv"], accept_multiple_files=True)
        if uploads and st.button("Ingest references", use_container_width=True):
            statuses = []
            for f in uploads:
                statuses.append(f"{f.name}: {ingest_reference(st.session_state.project, st.session_state.workspace, f, source_type, legal_note)}")
            st.success("References processed.")
            st.write(statuses)

    with st.expander("Engineering Tools", expanded=False):
        st.markdown("- Beam / Shaft / Bearing checks\n- Reynolds / pressure drop logic\n- Sheet metal bend allowance\n- Injection molding wall/rib checks")
        st.caption("Calculators auto-run when numeric inputs are detected in the chat.")

    with st.expander("Reports", expanded=False):
        md = memory_to_markdown(st.session_state.project)
        st.download_button("Download Markdown", data=md.encode("utf-8"), file_name=f"{slugify(st.session_state.project)}_report.md", mime="text/markdown", use_container_width=True)
        docx = make_docx_bytes(md)
        if docx:
            st.download_button("Download Word DOCX", data=docx, file_name=f"{slugify(st.session_state.project)}_report.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        pdf = make_pdf_bytes(md)
        if pdf:
            st.download_button("Download PDF", data=pdf, file_name=f"{slugify(st.session_state.project)}_report.pdf", mime="application/pdf", use_container_width=True)
        xlsx = make_xlsx_bytes(st.session_state.project)
        if xlsx:
            st.download_button("Download Excel XLSX", data=xlsx, file_name=f"{slugify(st.session_state.project)}_memory.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    with st.expander("Quality Tests", expanded=False):
        if st.button("Run internal evaluation", use_container_width=True):
            st.session_state.eval_results = run_quality_tests()
        if "eval_results" in st.session_state:
            st.write(st.session_state.eval_results)

    with st.expander("Settings", expanded=False):
        st.markdown(f"Mode: **Internal Knowledge Only**")
        st.markdown(f"Brain: **Mechanical Decision Engine v25**")
        st.markdown(f"Internal knowledge docs: **{len(list(KNOWLEDGE_DIR.glob('*/*.md')))}**")
        st.markdown(f"Project memory: `{project_dir(st.session_state.project).relative_to(ROOT)}`")
        st.markdown("External AI providers are not part of this build.")
        st.markdown(f"Build: `{APP_VERSION}`")
    st.markdown("---")
    st.caption("Wafeeq · MechAI Pro")

# -----------------------------------------------------------------------------
# Main view
# -----------------------------------------------------------------------------

if view == "About":
    st.title("MechAI Pro")
    st.markdown(
        """
### Mechanical Engineering Operating System — Knowledge-First Build

This build is not a wrapper around OpenAI or Gemini. Its visible reasoning path is:

`Knowledge Packs → Retrieval → Mechanical Reasoning → Risk/Scoring → Calculators → Project Memory → Reports`

**Engineering use note:** Always verify calculations, CAD automation, FEA/CFD assumptions, standards compliance, and physical test evidence before engineering release.
        """
    )
    st.stop()

# Landing
if not st.session_state.messages:
    st.markdown("<div style='height:18vh'></div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;font-weight:500'>Good to see you, Wafeeq.</h2>", unsafe_allow_html=True)

# Render chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("downloads"):
            for dl in msg["downloads"]:
                st.download_button(dl["label"], data=dl["data"], file_name=dl["file_name"], mime=dl["mime"], key=dl["key"])

prompt = st.chat_input("Ask anything engineering...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    frame = detect_problem_frame(prompt, st.session_state.workspace)
    sources = retrieve(prompt, frame.workspace, st.session_state.project, top_k=7)
    risks = build_risk_matrix(frame, prompt)
    calcs = engineering_calculators(prompt, frame)
    answer = build_answer(prompt, frame, sources, risks, calcs, project=st.session_state.project)
    downloads = []
    # CAD artifact
    if frame.workspace == "CAD / SolidWorks" or any(k in prompt.lower() for k in ["solidworks", "macro", "dxf", "step"]):
        macro = generate_solidworks_macro(prompt)
        validation = "\n".join(validate_macro(macro))
        answer += "\n\n#### CAD / SolidWorks artifact generated\n"
        answer += "- A `.bas` macro skeleton is available below. Review paths, backup files, and test on a copy before use.\n"
        answer += "\n**Macro validation**\n" + "\n".join([f"- {x}" for x in validate_macro(macro)])
        downloads.append({"label": "Download SolidWorks VBA .bas", "data": macro.encode("utf-8"), "file_name": "mechai_solidworks_macro.bas", "mime": "text/plain", "key": str(uuid.uuid4())})
        downloads.append({"label": "Download Macro Validation Notes", "data": validation.encode("utf-8"), "file_name": "macro_validation.txt", "mime": "text/plain", "key": str(uuid.uuid4())})
    # Simulation artifact
    if frame.workspace == "Simulation / FEA" or "ansys" in prompt.lower() or "fea" in prompt.lower():
        apdl = generate_apdl_plan(prompt)
        answer += "\n\n#### FEA artifact generated\n- ANSYS APDL starter skeleton is available below. Treat it as a setup scaffold, not release evidence.\n"
        downloads.append({"label": "Download ANSYS APDL .mac", "data": apdl.encode("utf-8"), "file_name": "mechai_ansys_static_structural.mac", "mime": "text/plain", "key": str(uuid.uuid4())})
    if frame.workspace == "CFD / Thermal" or "fluent" in prompt.lower() or "cfd" in prompt.lower():
        jou = generate_fluent_journal(prompt)
        answer += "\n\n#### CFD artifact generated\n- Fluent journal starter skeleton is available below. Validate domain, mesh, boundary conditions, y+, and convergence.\n"
        downloads.append({"label": "Download Fluent Journal .jou", "data": jou.encode("utf-8"), "file_name": "mechai_fluent_setup.jou", "mime": "text/plain", "key": str(uuid.uuid4())})
    append_memory(st.session_state.project, prompt, answer, frame, risks, calcs, sources)
    st.session_state.messages.append({"role": "assistant", "content": f"{WORKSPACES[frame.workspace]['icon']} **{frame.agent} · Internal Knowledge Only · Mechanical Engineering OS v25**\n\n" + answer, "downloads": downloads})
    st.rerun()
