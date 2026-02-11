import os
import json
import csv
import re

import fitz  # PyMuPDF
import pdfplumber

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

# =========================================================
# 1. Missing-space detection (whether to fallback to words)
# =========================================================

def has_long_english_token(text, threshold=20):
    return any(
        len(m.group()) >= threshold
        for m in re.finditer(r"[A-Za-z]+", text)
    )


def space_ratio(text):
    if not text:
        return 1.0
    return text.count(" ") / len(text)


def is_space_missing(text):
    signals = 0
    if has_long_english_token(text):
        signals += 1
    if space_ratio(text) < 0.08:
        signals += 1
    return signals >= 1


# =========================================================
# 2. Single-column text reconstruction (preserve order)
# =========================================================

def rebuild_text_from_words(words, x_tolerance=2, y_tolerance=3):
    if not words:
        return ""

    # Reading order: doctop -> x
    words = sorted(words, key=lambda w: (w["doctop"], w["x0"]))

    lines = []
    current_line = []
    current_y = None

    for w in words:
        y = w["top"]
        if current_y is None:
            current_y = y
        elif abs(y - current_y) > y_tolerance:
            lines.append(current_line)
            current_line = []
            current_y = y
        current_line.append(w)

    if current_line:
        lines.append(current_line)

    text_lines = []
    for line in lines:
        line = sorted(line, key=lambda w: w["x0"])
        parts = []
        prev_x1 = None

        for w in line:
            if prev_x1 is not None and (w["x0"] - prev_x1) > x_tolerance:
                parts.append(" ")
            parts.append(w["text"])
            prev_x1 = w["x1"]

        text_lines.append("".join(parts))

    return "\n".join(text_lines)


# =========================================================
# 3. Content-aware dual-column handling (core change)
# =========================================================

def rebuild_with_columns(words, page_width):
    """Split words into two columns at page center and rebuild text."""
    split_x = page_width * 0.5

    # Dual-column body
    left = [w for w in words if w["x0"] < split_x]
    right = [w for w in words if w["x0"] >= split_x]

    left_text = rebuild_text_from_words(left)
    right_text = rebuild_text_from_words(right)

    return left_text + "\n\n" + right_text


# =========================================================
# 4. Main parser
# =========================================================

def parse_pdf(path, filename, layout_type="single"):
    """Parse PDF into text, tables, and images.
    
    Args:
        path: File path to PDF
        filename: PDF filename
        layout_type: "single" for single-column or "dual" for two-column layout
    """
    base_dir = os.path.dirname(path)
    basename = os.path.splitext(filename)[0]
    basename = basename.replace(" ", "_")  # Sanitize for directory name
    process_dir = os.path.join(base_dir, "process", f"{basename}__pdf")
    os.makedirs(process_dir, exist_ok=True)
    texts = []
    tables_info = []
    images_info = []

    # -------------------------------
    # Text
    # -------------------------------
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            raw_text = page.extract_text(
                x_tolerance=2,
                y_tolerance=3,
                use_text_flow=True
            ) or ""

            # Decide text extraction method based on layout_type
            if layout_type == "dual":
                # For dual column: always extract words and rebuild by columns
                words = page.extract_words(
                    x_tolerance=2,
                    y_tolerance=3,
                    keep_blank_chars=False
                )
                text = rebuild_with_columns(words, page.width)
            else:
                # For single column: use raw text, but fallback if spaces missing
                if is_space_missing(raw_text):
                    words = page.extract_words(
                        x_tolerance=2,
                        y_tolerance=3,
                        keep_blank_chars=False
                    )
                    text = rebuild_text_from_words(words)
                else:
                    text = raw_text

            texts.append(text)

            with open(
                os.path.join(process_dir, f"page_{i}.txt"),
                "w",
                encoding="utf-8"
            ) as f:
                f.write(text)

    # -------------------------------
    # Images
    # -------------------------------
    doc = fitz.open(path)
    for p_idx in range(len(doc)):
        page = doc[p_idx]
        for img_idx, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            try:
                base = doc.extract_image(xref)
                img_bytes = base["image"]
                ext = base.get("ext", "png")
                img_name = f"page_{p_idx+1}_img_{img_idx}.{ext}"
                img_path = os.path.join(process_dir, img_name)

                with open(img_path, "wb") as f:
                    f.write(img_bytes)

                images_info.append({
                    "page": p_idx + 1,
                    "img_index": img_idx,
                    "path": img_path,
                    "width": base.get("width"),
                    "height": base.get("height")
                })
            except Exception:
                continue
    doc.close()

    # -------------------------------
    # Summary
    # -------------------------------
    full_text_path = os.path.join(process_dir, "full_text.txt")
    with open(full_text_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(texts))

    summary = {
        "text_files": [
            os.path.join(process_dir, f"page_{i}.txt")
            for i in range(1, len(texts) + 1)
        ],
        "full_text": full_text_path,
        "tables": tables_info,
        "images": images_info
    }

    with open(
        os.path.join(process_dir, "summary.json"),
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return process_dir, summary
