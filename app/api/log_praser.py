from __future__ import annotations

from typing import Any, Dict, List, Optional


def _find_check(
    checks: List[Dict[str, Any]],
    *,
    check_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    for item in checks:
        if not isinstance(item, dict):
            continue
        if check_type is not None and item.get("check_type") == check_type:
            return item
    return None


def parse_check_log(raw: Dict[str, Any], *, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Post-process raw check results into UI sections.

    Sections:
      1. file_info
      2. image_info
      3. cross_ref_info
      4. pdf_metadata
      5. anonymity_check
      6. hidden_prompt_check
      7. summary_info
    """
    context = context or {}
    checks = raw.get("checks", []) if isinstance(raw, dict) else []

    file_info = {
        "available": True,
        "results": [{
            "filename": raw.get("filename") if isinstance(raw, dict) else None,
            "process_dir": context.get("process_dir"),
            "file_path": context.get("file_path"),
            "checks_count": len(checks) if isinstance(checks, list) else 0,
            "confidence": "Basic"
        }],
    }

    link_check = _find_check(checks, check_type="links")
    if link_check:
        link_info = {
            "available": True,
            "results": link_check.get("results"),
        }
    else:
        link_info = {
            "available": False,
            "results": "link anonymization check not run",
        }

    image_check = _find_check(checks, check_type="images")
    if image_check:
        image_info = {
            "available": True,
            "results": image_check.get("results"),
        }
    else:
        image_info = {
            "available": False,
            "results": "image_quality check not run",
        }

    cross_ref_check = _find_check(checks, check_type="cross_ref")
    if cross_ref_check:
        cross_ref_info = {
            "available": True,
            "results": cross_ref_check.get("results"),
        }
    else:
        cross_ref_info = {
            "available": False,
            "results": "cross_ref check not run",
        }

    metadata_check = _find_check(checks, check_type="metadata")
    if metadata_check:
        pdf_metadata = {
            "available": True,
            "results": metadata_check.get("results"),
        }
    else:
        pdf_metadata = {
            "available": False,
            "results": "metadata check not run",
        }

    anonymous_check = _find_check(checks, check_type="anonymous")
    if anonymous_check:
        anonymity_check = {
            "available": True,
            "results": anonymous_check.get("results"),
        }
    else:
        anonymity_check = {
            "available": False,
            "results": "anonymous LLM check not run",
        }

    hidden_check = _find_check(checks, check_type="hidden")
    if hidden_check:
        hidden_prompt_check = {
            "available": True,
            "results": hidden_check.get("results"),
        }
    else:
        hidden_prompt_check = {
            "available": False,
            "results": "hidden prompt LLM check not run",
        }

    summary_check = _find_check(checks, check_type="summary")
    if summary_check:
        summary_info = {
            "available": True,
            "results": summary_check.get("results"),
        }
    else:
        summary_info = {
            "available": False,
            "results": "summary not run",
        }

    return {
        "file_info": file_info,
        "image_info": image_info,
        "link_info": link_info,
        "cross_ref_info": cross_ref_info,
        "pdf_metadata": pdf_metadata,
        "anonymity_check": anonymity_check,
        "hidden_prompt_check": hidden_prompt_check,
        "summary_info": summary_info,
    }
