# -*- coding: utf-8 -*-
"""
Quick test for MechAI Pro v17 internal knowledge engine.
Run:
    py test_knowledge_engine_v17.py
"""

from knowledge_engine_v17 import retrieve_knowledge, format_knowledge_context

tests = [
    ("Create a DFM review for an injection molded plastic cover", "Manufacturing / DFM"),
    ("How should I set up mesh convergence for an ANSYS bracket simulation?", "Simulation / FEA"),
    ("Select material for a lightweight corrosion resistant cover", "Materials selection"),
    ("Write a SolidWorks macro to export DXF files", "CAD / SolidWorks"),
    ("Calculate Reynolds number and pressure drop for water flow", "CFD / Thermal"),
]

for q, ws in tests:
    print("=" * 90)
    print("Workspace:", ws)
    print("Query:", q)
    hits = retrieve_knowledge(q, workspace=ws, top_k=3)
    print(format_knowledge_context(hits))
    print()
