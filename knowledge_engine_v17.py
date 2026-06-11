# -*- coding: utf-8 -*-
"""
MechAI Pro v17 - Internal Knowledge Search Engine

Goal:
- Make MechAI knowledge-first.
- Search internal workspace knowledge packs before using OpenAI/Gemini.
- No external API required.
- Works locally and on Streamlit Cloud.

Folders expected:
knowledge_packs/
  mechanical_design/notes.md
  cad_solidworks/notes.md
  simulation_fea/notes.md
  cfd_thermal/notes.md
  manufacturing_dfm/notes.md
  materials_selection/notes.md
  innovation_patent/notes.md

Optional:
knowledge_packs/<pack>/source_docs/*.md
knowledge_packs/<pack>/source_docs/*.txt
knowledge_packs/<pack>/source_docs/*.pdf
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import re
from typing import Dict, Iterable, List, Optional, Tuple


WORKSPACE_TO_PACK: Dict[str, str] = {
    "General engineering": "",
    "Product R&D / Design": "mechanical_design",
    "CAD / SolidWorks": "cad_solidworks",
    "Simulation / FEA": "simulation_fea",
    "CFD / Thermal": "cfd_thermal",
    "Manufacturing / DFM": "manufacturing_dfm",
    "Materials selection": "materials_selection",
    "Innovation / Patent": "innovation_patent",

    # Arabic / mixed labels, if used later
    "تصميم وتطوير": "mechanical_design",
    "سوليدووركس": "cad_solidworks",
    "محاكاة FEA": "simulation_fea",
    "موائع CFD": "cfd_thermal",
    "تصنيع DFM": "manufacturing_dfm",
    "اختيار مواد": "materials_selection",
    "ابتكار وبراءات": "innovation_patent",
}


INTENT_KEYWORDS: Dict[str, List[str]] = {
    "mechanical_design": [
        "design", "shaft", "bearing", "spring", "gear", "stress", "strain",
        "fatigue", "load", "safety", "factor", "tolerance", "gd&t", "mechanical",
        "failure", "bracket", "housing", "wall", "thickness", "mechanism"
    ],
    "cad_solidworks": [
        "solidworks", "macro", "vba", "api", "part", "assembly", "drawing",
        "bom", "step", "dxf", "sketch", "feature", "extrude", "cad"
    ],
    "simulation_fea": [
        "fea", "simulation", "ansys", "static", "modal", "buckling", "mesh",
        "boundary", "condition", "contact", "convergence", "stress plot",
        "finite", "element"
    ],
    "cfd_thermal": [
        "cfd", "fluent", "flow", "thermal", "heat", "pressure", "drop",
        "reynolds", "turbulence", "y+", "mesh", "convection", "fluid", "pipe"
    ],
    "manufacturing_dfm": [
        "dfm", "dfa", "manufacturing", "injection", "molding", "moulding",
        "machining", "sheet", "metal", "tooling", "cycle", "time", "scrap",
        "assembly", "tolerance", "cost"
    ],
    "materials_selection": [
        "material", "materials", "ashby", "asm", "steel", "aluminum", "plastic",
        "abs", "pc", "pp", "nylon", "strength", "stiffness", "density",
        "corrosion", "temperature", "datasheet"
    ],
    "innovation_patent": [
        "patent", "prior", "art", "claim", "innovation", "invention", "triz",
        "novelty", "prototype", "commercial", "wipo", "uspto"
    ],
}


@dataclass
class KnowledgeDocument:
    pack: str
    title: str
    path: str
    text: str


@dataclass
class KnowledgeHit:
    pack: str
    title: str
    path: str
    score: float
    snippet: str


def normalize_workspace(workspace: Optional[str]) -> str:
    if not workspace:
        return ""
    return WORKSPACE_TO_PACK.get(workspace, workspace if workspace in INTENT_KEYWORDS else "")


def tokenize(text: str) -> List[str]:
    text = text.lower()
    # Keep English words, numbers, and simple Arabic character ranges
    return re.findall(r"[a-z0-9\+\#\.\-/]+|[\u0600-\u06FF]+", text)


def split_into_chunks(text: str, max_chars: int = 1200, overlap: int = 160) -> List[str]:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) <= max_chars:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        # Prefer ending at paragraph boundary
        para_end = text.rfind("\n\n", start, end)
        if para_end > start + max_chars * 0.45:
            end = para_end
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def read_pdf_text(path: Path) -> str:
    try:
        import PyPDF2  # type: ignore
        reader = PyPDF2.PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages[:80]):
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(pages)
    except Exception:
        return ""


def read_text_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return read_pdf_text(path)
    if suffix in {".md", ".txt", ".json", ".csv"}:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
    return ""


def load_knowledge_documents(base_dir: str | Path = "knowledge_packs") -> List[KnowledgeDocument]:
    base = Path(base_dir)
    if not base.exists():
        return []

    docs: List[KnowledgeDocument] = []

    for pack_dir in sorted([p for p in base.iterdir() if p.is_dir()]):
        pack = pack_dir.name

        candidate_files: List[Path] = []
        notes = pack_dir / "notes.md"
        if notes.exists():
            candidate_files.append(notes)

        source_docs = pack_dir / "source_docs"
        if source_docs.exists():
            for ext in ("*.md", "*.txt", "*.json", "*.csv", "*.pdf"):
                candidate_files.extend(source_docs.rglob(ext))

        for file_path in candidate_files:
            raw = read_text_file(file_path).strip()
            if not raw:
                continue
            title = file_path.stem.replace("_", " ").title()
            for idx, chunk in enumerate(split_into_chunks(raw)):
                docs.append(
                    KnowledgeDocument(
                        pack=pack,
                        title=f"{title} #{idx + 1}",
                        path=str(file_path).replace("\\", "/"),
                        text=chunk,
                    )
                )

    return docs


def infer_pack_from_query(query: str) -> str:
    q_tokens = set(tokenize(query))
    scores: Dict[str, int] = {}
    for pack, words in INTENT_KEYWORDS.items():
        score = 0
        for w in words:
            wt = tokenize(w)
            if all(t in q_tokens for t in wt):
                score += 2 if len(wt) > 1 else 1
        scores[pack] = score
    best_pack, best_score = max(scores.items(), key=lambda x: x[1])
    return best_pack if best_score > 0 else ""


def score_document(query: str, doc: KnowledgeDocument, preferred_pack: str = "") -> float:
    q_tokens = tokenize(query)
    if not q_tokens:
        return 0.0

    doc_tokens = tokenize(doc.text)
    if not doc_tokens:
        return 0.0

    tf: Dict[str, int] = {}
    for t in doc_tokens:
        tf[t] = tf.get(t, 0) + 1

    score = 0.0
    unique_q = set(q_tokens)

    for t in unique_q:
        if t in tf:
            # lightweight tf scoring
            score += 1.0 + math.log(1 + tf[t])

    # Small phrase bonus for important engineering phrases
    q_lower = query.lower()
    d_lower = doc.text.lower()
    for phrase in [
        "injection molding", "pressure drop", "mesh convergence", "solidworks macro",
        "material selection", "design for manufacturing", "finite element",
        "boundary conditions", "safety factor", "wall thickness"
    ]:
        if phrase in q_lower and phrase in d_lower:
            score += 4.0

    if preferred_pack and doc.pack == preferred_pack:
        score *= 1.45

    # Pack inferred from query gets a smaller boost even if user selected General
    inferred = infer_pack_from_query(query)
    if inferred and doc.pack == inferred:
        score *= 1.25

    return score


def make_snippet(text: str, query: str, max_len: int = 520) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text

    q_tokens = tokenize(query)
    positions = []
    lower = text.lower()
    for t in q_tokens:
        pos = lower.find(t.lower())
        if pos >= 0:
            positions.append(pos)
    center = min(positions) if positions else 0
    start = max(0, center - max_len // 3)
    end = min(len(text), start + max_len)
    return ("..." if start > 0 else "") + text[start:end].strip() + ("..." if end < len(text) else "")


def retrieve_knowledge(
    query: str,
    workspace: Optional[str] = None,
    top_k: int = 4,
    base_dir: str | Path = "knowledge_packs",
) -> List[KnowledgeHit]:
    docs = load_knowledge_documents(base_dir)
    if not docs:
        return []

    preferred_pack = normalize_workspace(workspace)
    scored: List[Tuple[float, KnowledgeDocument]] = []
    for doc in docs:
        score = score_document(query, doc, preferred_pack=preferred_pack)
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    hits: List[KnowledgeHit] = []
    seen_paths = set()
    for score, doc in scored:
        # Keep diversity: avoid returning too many chunks from same path
        key = (doc.path, doc.title)
        if key in seen_paths:
            continue
        seen_paths.add(key)
        hits.append(
            KnowledgeHit(
                pack=doc.pack,
                title=doc.title,
                path=doc.path,
                score=round(score, 3),
                snippet=make_snippet(doc.text, query),
            )
        )
        if len(hits) >= top_k:
            break

    return hits


def format_knowledge_context(hits: List[KnowledgeHit]) -> str:
    if not hits:
        return "No internal knowledge hits found."

    lines = ["Internal knowledge retrieved:"]
    for i, hit in enumerate(hits, start=1):
        lines.append(
            f"[K{i}] Pack: {hit.pack} | Source: {hit.path} | Score: {hit.score}\n"
            f"{hit.snippet}"
        )
    return "\n\n".join(lines)


def compose_internal_answer(query: str, workspace: Optional[str] = None, hits: Optional[List[KnowledgeHit]] = None) -> str:
    hits = hits if hits is not None else retrieve_knowledge(query, workspace=workspace)

    if not hits:
        return (
            "I could not find enough internal knowledge for this question yet.\n\n"
            "Recommended next action: add a relevant PDF, datasheet, standard extract, or company note into the correct "
            "`knowledge_packs/<workspace>/source_docs` folder, then rebuild/test the knowledge search."
        )

    source_lines = "\n".join([f"- [{i+1}] {h.pack}: `{h.path}`" for i, h in enumerate(hits)])

    return (
        "Based on the internal MechAI knowledge packs, here is the grounded starting point:\n\n"
        f"{format_knowledge_context(hits)}\n\n"
        "Engineering use note:\n"
        "- Treat this as internal reference guidance, not a certified calculation.\n"
        "- For design release, validate assumptions, calculations, standards compliance, and test evidence.\n\n"
        "Sources used:\n"
        f"{source_lines}"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test MechAI internal knowledge search.")
    parser.add_argument("query", nargs="*", help="Question to search for.")
    parser.add_argument("--workspace", default="General engineering", help="Workspace label.")
    parser.add_argument("--top-k", type=int, default=4)
    args = parser.parse_args()

    q = " ".join(args.query).strip() or "DFM review for injection molded plastic cover"
    hits = retrieve_knowledge(q, workspace=args.workspace, top_k=args.top_k)
    print(compose_internal_answer(q, workspace=args.workspace, hits=hits))
