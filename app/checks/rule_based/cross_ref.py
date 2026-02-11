import os
import json
import re
from typing import Dict, List, Set


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        with open(path, "r", encoding="latin-1", errors="ignore") as f:
            return f.read()


def _strip_comments(text: str) -> str:
    cleaned = []
    for line in text.splitlines():
        line = re.sub(r"(?<!\\)%.*", "", line)
        cleaned.append(line)
    return "\n".join(cleaned)


def _extract_refs(text: str) -> Set[str]:
    pattern = re.compile(r"\\(ref|eqref)\s*\{([^}]+)\}")
    refs = set()
    for match in pattern.finditer(text):
        refs.add(match.group(2).strip())
    return refs


def _extract_labels(text: str) -> Set[str]:
    pattern = re.compile(r"\\label\s*\{([^}]+)\}")
    labels = set()
    for match in pattern.finditer(text):
        labels.add(match.group(1).strip())
    return labels


def _extract_env_blocks(text: str, env_name: str) -> List[str]:
    pattern = re.compile(
        r"\\begin\{" + re.escape(env_name) + r"\}(.*?)\\end\{" + re.escape(env_name) + r"\}",
        re.DOTALL,
    )
    return [m.group(1) for m in pattern.finditer(text)]


def _labels_in_blocks(blocks: List[str]) -> Set[str]:
    labels = set()
    for block in blocks:
        labels.update(_extract_labels(block))
    return labels


def _load_full_text_path(proj_path: str) -> str | None:
    if not proj_path or not os.path.isdir(proj_path):
        return None
    summary_path = os.path.join(proj_path, "summary.json")
    if not os.path.exists(summary_path):
        return None
    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        return summary.get("full_text")
    except Exception:
        return None


def cross_ref_check(file_path: str, proj_path: str) -> Dict:
    """Check LaTeX references consistency using merged full text.

    Rules:
      1) All \\ref/\\eqref targets must exist in \\label declarations.
      2) All labels inside figure/table environments must be referenced.
    """
    if file_path[-4:].lower() == ".pdf":
        return {
            "check_type": "cross_ref",
            "results": "Input is a PDF file, cross-ref check requires LaTeX source"
        }
    full_text_path = _load_full_text_path(proj_path)
    if not full_text_path:
        return {
            "check_type": "cross_ref",
            "results": "summary.json/full_text not found in process directory"
        }

    raw_text = _read_text(full_text_path)
    text = _strip_comments(raw_text)

    refs = _extract_refs(text)
    labels = _extract_labels(text)

    invalid_refs = sorted(refs - labels)

    figure_blocks = _extract_env_blocks(text, "figure")
    table_blocks = _extract_env_blocks(text, "table")
    fig_labels = _labels_in_blocks(figure_blocks)
    table_labels = _labels_in_blocks(table_blocks)
    fig_table_labels = fig_labels | table_labels

    unreferenced = sorted(fig_table_labels - refs)

    passed = len(invalid_refs) == 0 and len(unreferenced) == 0

    return {
        "check_type": "cross_ref",
        "results": [
                {
                    "invalid_refs": invalid_refs,
                    "confidence": "high"
                },
                {
                    "unreferenced_fig_table_labels": unreferenced,
                    "confidence": "medium"
                },
                {
                    "1. refs_count": len(refs),
                    "2. figure_labels_count": len(fig_labels),
                    "3. table_labels_count": len(table_labels),
                    "confidence": "Statistics"
                },
            ]
    }

