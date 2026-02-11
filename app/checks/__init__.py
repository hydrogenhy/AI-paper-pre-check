from app.checks.rule_based.image_quality import image_quality_check
from app.checks.rule_based.link_extractor import check_links_existence
from app.checks.rule_based.metadata import extract_metadata
from app.checks.rule_based.cross_ref import cross_ref_check
from app.checks.llm_based.llm_check import llm_check, llm_summary
import json


DEFAULT_CHECKS = {"image_quality", "link_anonymization", "pdf_metadata", "cross_ref"}


def run_checks(file_path, proj_path, filename, text, enabled_checks=None):
    checks = []
    enabled = DEFAULT_CHECKS if enabled_checks is None else set(enabled_checks)

    if "image_quality" in enabled:
        image_res = image_quality_check(proj_path)
        checks.append(image_res)

    if "link_anonymization" in enabled:
        links_res = check_links_existence(text)
        checks.append(links_res)

    if "pdf_metadata" in enabled:
        meta_res = extract_metadata(file_path)
        checks.append(meta_res)

    if "cross_ref" in enabled:
        cross_res = cross_ref_check(file_path, proj_path)
        checks.append(cross_res)

    if "anonymity" in enabled:
        anonymous_res = llm_check(file_path, "anonymous")
        checks.append(anonymous_res)

    if "hidden_prompt" in enabled:
        hidden_res = llm_check(file_path, "hidden")
        checks.append(hidden_res)

        
    if "summary" in enabled:
        summary_res = llm_summary(str(checks))
        checks.append(summary_res)

    save_path = proj_path + "/check_results.json"
    with open(save_path, "w") as f:
        json.dump(checks, f, indent=4)

    return {"filename": filename, "checks": checks}
