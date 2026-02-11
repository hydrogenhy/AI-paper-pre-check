import json
import os
import re
import zipfile
from typing import Dict, List, Tuple


def _safe_extract_zip(zip_path: str, dest_dir: str) -> List[str]:
    extracted = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            name = member.filename
            if not name or name.endswith("/"):
                continue
            target_path = os.path.normpath(os.path.join(dest_dir, name))
            if not os.path.abspath(target_path).startswith(os.path.abspath(dest_dir) + os.sep):
                continue
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with zf.open(member, "r") as src, open(target_path, "wb") as dst:
                dst.write(src.read())
            extracted.append(target_path)
    return extracted


def _normalize_dir_names(root_dir: str) -> None:
    for current_root, dirnames, _ in os.walk(root_dir, topdown=False):
        for dirname in dirnames:
            if " " not in dirname:
                continue
            src = os.path.join(current_root, dirname)
            dst = os.path.join(current_root, dirname.replace(" ", "_"))
            if os.path.abspath(src) == os.path.abspath(dst):
                continue
            if os.path.exists(dst):
                continue
            os.rename(src, dst)


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
        # Remove unescaped % comments
        line = re.sub(r"(?<!\\)%.*", "", line)
        cleaned.append(line)
    return "\n".join(cleaned)


def _normalize_ref_dirs(ref: str) -> str:
    parts = re.split(r"[\\/]+", ref)
    if len(parts) <= 1:
        return ref
    dir_parts = [p.replace(" ", "_") for p in parts[:-1]]
    return "/".join(dir_parts + [parts[-1]])


def _resolve_tex_path(base_dir: str, project_root: str, ref: str) -> str:
    ref = ref.strip().strip('"').strip("'")
    candidates = []
    if os.path.isabs(ref):
        candidates.append(ref)
    else:
        refs = [ref]
        normalized_ref = _normalize_ref_dirs(ref)
        if normalized_ref != ref:
            refs.append(normalized_ref)
        for r in refs:
            candidates.append(os.path.join(base_dir, r))
            if project_root and os.path.abspath(project_root) != os.path.abspath(base_dir):
                candidates.append(os.path.join(project_root, r))

    expanded = []
    for cand in candidates:
        cand = os.path.normpath(cand)
        root, ext = os.path.splitext(cand)
        if ext:
            expanded.append(cand)
        else:
            expanded.append(cand + ".tex")
            expanded.append(cand)

    for path in expanded:
        if os.path.exists(path):
            return path

    return os.path.normpath(candidates[0]) if candidates else ref


def _resolve_graphics_paths(base_dir: str, project_root: str, ref: str) -> List[str]:
    ref = ref.strip().strip('"').strip("'")
    candidates: List[str] = []
    if os.path.isabs(ref):
        candidates.append(ref)
    else:
        refs = [ref]
        normalized_ref = _normalize_ref_dirs(ref)
        if normalized_ref != ref:
            refs.append(normalized_ref)
        for r in refs:
            candidates.append(os.path.join(base_dir, r))
            if project_root and os.path.abspath(project_root) != os.path.abspath(base_dir):
                candidates.append(os.path.join(project_root, r))
    expanded: List[str] = []
    for cand in candidates:
        cand = os.path.normpath(cand)
        root, ext = os.path.splitext(cand)
        if ext:
            expanded.append(cand)
        else:
            expanded.extend([
                cand + ".png",
                cand + ".jpg",
                cand + ".jpeg",
                cand + ".pdf",
                cand + ".eps",
                cand,
            ])
    return [os.path.abspath(p) for p in expanded if p]


def _extract_graphics_paths(text: str, base_dir: str, project_root: str) -> List[Dict]:
    images = []
    pattern = re.compile(r"\\includegraphics(?:\s*\[[^\]]*\])?\s*\{([^}]+)\}")
    for match in pattern.finditer(text):
        raw_path = match.group(1).strip()
        candidates = _resolve_graphics_paths(base_dir, project_root, raw_path)
        resolved = next((p for p in candidates if os.path.exists(p)), None)
        images.append(
            {
                "path": raw_path,
                "resolved_path": resolved,
            }
        )
    return images


def _expand_inputs(path: str, project_root: str, visited: set) -> Tuple[str, List[Dict]]:
    abs_path = os.path.abspath(path)
    if abs_path in visited:
        return "", []
    visited.add(abs_path)

    base_dir = os.path.dirname(path)
    raw_text = _read_text(path)
    text = _strip_comments(raw_text)

    images = _extract_graphics_paths(text, base_dir, project_root)

    # Avoid matching \includegraphics as \include
    input_pattern = re.compile(r"\\(input|include)(?!graphics)\s*(\{([^}]+)\}|([^\s%]+))")

    def replace(match: re.Match) -> str:
        ref = match.group(3) or match.group(4) or ""
        target = _resolve_tex_path(base_dir, project_root, ref)
        if not os.path.exists(target):
            return f"\n% [Missing input: {ref}]\n"
        nested_text, nested_images = _expand_inputs(target, project_root, visited)
        images.extend(nested_images)
        return "\n" + nested_text + "\n"

    expanded = input_pattern.sub(replace, text)
    return expanded, images


def _find_main_tex(tex_files: List[str]) -> str:
    candidates = []
    for path in tex_files:
        try:
            content = _read_text(path)
        except Exception:
            continue
        if re.search(r"\\begin\s*\{document\}", content):
            candidates.append(path)
    if not candidates:
        raise ValueError("No main .tex file with \\begin{document} found")
    candidates.sort(key=lambda p: (len(p), p))
    return candidates[0]


def parse_latex_zip(path: str, filename: str) -> Tuple[str, Dict]:
    """Extract LaTeX zip and build a merged text file.

    Steps:
      1) Extract zip into uploads/process/<basename>
      2) Find main .tex with \\begin{document}
      3) Expand \\input/\\include into a single text file
      4) Collect \\includegraphics paths
      5) Save summary.json
    """
    base_dir = os.path.dirname(path)
    basename = os.path.splitext(filename)[0].replace(" ", "_")
    process_dir = os.path.join(base_dir, "process", f"{basename}__latex")
    os.makedirs(process_dir, exist_ok=True)

    _safe_extract_zip(path, process_dir)
    _normalize_dir_names(process_dir)

    tex_files = []
    for root, _, files in os.walk(process_dir):
        for name in files:
            if name.lower().endswith(".tex"):
                tex_files.append(os.path.join(root, name))

    main_tex = _find_main_tex(tex_files)

    merged_text, images = _expand_inputs(main_tex, process_dir, visited=set())

    full_text_path = os.path.join(process_dir, f"full_text.txt")
    with open(full_text_path, "w", encoding="utf-8") as f:
        f.write(merged_text)

    summary = {
        "text_files": tex_files,
        "full_text": full_text_path,
        "tables": [],
        "images": images,
        "main_tex": main_tex,
    }

    with open(os.path.join(process_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return process_dir, summary
