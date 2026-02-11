import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from app.checks.llm_based.prompts import PRESETS
from app.checks.llm_based.model import _request_openai_text, llm_to_json
import json

def llm_check(file_path: str, check_type: str) -> dict:
    with open("app\checks\llm_based\config.json", "r") as f:
        config = f.read()
    config = json.loads(config)
    file_path = file_path.replace("\\", "/")  # debug
    try:
        response_text = _request_openai_text(
            file_path=file_path,
            base_url=config.get("api_base"),
            api_key=config.get("api_key"),
            model=config.get("model_name"),
            prompt=PRESETS[check_type],
            system_prompt=PRESETS["system"],
        )
        return {"check_type": check_type, "results": llm_to_json(response_text)}
    except Exception as e:
        return {"check_type": check_type, "results": str(e)}
    

def llm_summary(check_log: str) -> str:
    with open("app\checks\llm_based\config.json", "r") as f:
        config = f.read()
    config = json.loads(config)
    try:
        response_text = _request_openai_text(
            base_url=config.get("api_base"),
            api_key=config.get("api_key"),
            model=config.get("model_name"),
            prompt=PRESETS["summary"],
            system_prompt=PRESETS["system"],
            summary=True,
            check_logs=check_log
        )
        return {"check_type": "summary", "results": response_text}
    except Exception as e:
        return {"check_type": "summary", "results": str(e)}
    
if __name__ == "__main__":
    result = llm_summary("""
                [{'check_type': 'images', 'results': {'images': [{'filename': 'page_2_img_1.png', 'width': 460, 'height': 471, 'dpi_x': 96.012, 'dpi_y': 96.012}], 'note': "DPI means the image's embedded metadata, NOT the PDF print DPI."}}, {'check_type': 'links', 'results': {'links_found': 1, 'links': ['https://github.com/real-username/private-research-project'], 'has_http_links': True}}, {'check_type': 'metadata', 'results': {'/Author': 'David S. Hippocampus', '/CreationDate': 'D:20260211092316Z', '/Creator': 'LaTeX with hyperref', '/Keywords': '', '/ModDate': 'D:20260211092316Z', '/PTEX.Fullbanner': 'This is pdfTeX, Version 3.141592653-2.6-1.40.27 (TeX Live 2025) kpathsea version 6.4.1', '/Producer': 'pdfTeX-1.40.27', '/Subject': '', '/Title': '', '/Trapped': '/False'}}, {'check_type': 'cross_ref', 'results': 'Input is a PDF file, cross-ref check requires LaTeX source'}]                         
            """)
    print(result)