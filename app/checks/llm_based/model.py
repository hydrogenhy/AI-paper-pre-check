import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import json
from typing import Any, Optional
from openai import OpenAI
import re

def llm_to_json(response: str) -> dict[str, Any]:
    """
    Parse LLM response containing a fenced ```json code block
    and return a dict suitable for frontend visualization.
    """
    try:
        if "```json" in response:  # deepseek style
            pattern = r"```json\s*(.*?)\s*```"
            match = re.search(pattern, response, re.DOTALL)
            json_str = match.group(1)
            parsed = json.loads(json_str)

        else:  # qwen style
            parsed = json.loads(response)

    except json.JSONDecodeError as e:
        parsed = response

    return parsed

def get_content(file_path: str) -> str:
    if file_path[-4:].lower() == ".pdf":
        file_path = file_path.replace("/uploads/", "/uploads/process/").rsplit(".", 1)[0]
        file_path = file_path + "__pdf/full_text.txt"
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def _build_openai_client(base_url: str, api_key: str | None):
    return OpenAI(api_key=api_key, base_url=base_url)

def _request_openai_text(
    *,
    file_path: str | None = None,
    base_url: str,
    api_key: str | None,
    model: str,
    prompt: str,
    system_prompt: Optional[str] = None,
    summary: bool = False,
    check_logs: str | None = None
) -> str | None:
    client = _build_openai_client(base_url, api_key)
    if not summary:
        if file_path[-4:].lower() != ".pdf":
            file_path = file_path.replace("/uploads/", "/uploads/process/").rsplit(".", 1)[0] + "__latex/full_text.txt"
        try:
            with open(file_path, "rb") as f:
                raw_file = client.files.create(
                    file=f,
                    purpose="file-extract",
                )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "system", "content": f'fileid://{raw_file.id}'},   # qwen-long style file input
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
        except Exception as e:  # deepseek not support file upload
            print(f"Error uploading file to OpenAI: {e}, upload via text in prompt")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": prompt + "\n\nfile content below:\n\n" + get_content(file_path)
                    }
                ],
            )
    
    elif summary:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": prompt + "\n\ncheck results below:\n\n" + check_logs
                }
            ],
        )

    content = response.choices[0].message.content if response.choices else None
    if isinstance(content, list):
        text_chunks = [c.get("text", "") for c in content if isinstance(c, dict)]
        content = "\n".join(text_chunks)
    if isinstance(content, str):
        return content
    return None

if __name__ == "__main__":
    from app.checks.llm_based.prompts import PRESETS
    with open("app\checks\llm_based\config.json", "r") as f:
        config = f.read()
    import json
    config = json.loads(config)
    result = _request_openai_text(
        file_path="./uploads/check_test.pdf",
        base_url=config["api_base"],
        api_key=config["api_key"],
        model=config["model_name"],
        prompt=PRESETS["anonymous"],
        system_prompt=PRESETS["system"],
    )
    print("LLM response:", result)