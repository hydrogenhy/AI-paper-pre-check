<p align="center">
  <img src="figs/head.png" width="50%">
</p>

# 🧪 AI Double-Blind Submission Pre-check

A lightweight web app for double -blind pre-submission checks on academic papers.  
It accepts **PDF** or **LaTeX ZIP** uploads, parses content, and runs rule-based + LLM-based checks to catch common issues before submission.

## ✨ Features

- PDF parsing with page-level text extraction
- LaTeX ZIP extraction and merged full-text generation
- Rule-based checks: image info, link extraction, PDF metadata, LaTeX cross-ref validation
- LLM-based checks: anonymity risk detection, hidden prompt injection detection
- Summaries of detection results with suggested revisions

## 🧭 Project Structure

- `app/main.py` — Flask application entry point
- `app/api/upload.py` — file upload + parser selection
- `app/api/check.py` — run checks and return structured results
- `app/services/pdf_parser.py` — PDF parsing to `uploads/process/...`
- `app/services/latex_parser.py` — LaTeX ZIP parsing + merged text
- `app/checks/` — rule-based and LLM-based checks
- `app/templates/index.html` — UI

## ⚙️ Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app\main.py
```

Open:
```
http://127.0.0.1:8000/
```

## 🤖 LLM Configuration

To enable LLM checks, configure:

`app/checks/llm_based/config.json`

### Example:

```json
{
  "api_key": "YOUR_API_KEY",
  "api_base": "https://api.deepseek.com/v1",
  "model_name": "deepseek-chat"
}
```

### Notes:
- `api_key` is required for LLM checks.
- `api_base` and `model_name` must match your provider.
- If the model does not support file uploads, the file content is included as part of the prompt instead (see `model.py`, line 72). The specific behavior can be determined from the controller output.

### Support:

Currently, two types of models are supported. To add support for other models, you need to update the JSON configuration file `app/checks/llm_based/config.json` and modify the request message format (including file upload) in `app/checks/llm_based/model.py` according to the model’s official API documentation. Additionally, if the model supports JSON output, the `llm_to_json()` parsing logic may need to be updated.

| model name | base url | supports JSON output | supports file upload |
|------------|----------|----------------------|----------------------|
| qwen-long | https://dashscope.aliyuncs.com/compatible-mode/v1 | Yes | Yes |
| deepseek-chat | https://api.deepseek.com/v1 | Yes | No |


## 🔁 Workflow

1. Upload a **PDF** or **LaTeX ZIP** file.
2. The server parses content into `uploads/process/<project_name>__/`. (This project provides two examples.)
3. Choose checks in the UI.
4. View detailed results and recommendations.

## 📄 Output Files

After the checks complete, the system writes a `check_results.json` file to:

```
uploads/process/<project_name>__{File Type}/check_results.json
```

This file provides the complete, structured output of all detection checks.


## 📦 Supported Upload Types

- **PDF** (`.pdf`)
- **LaTeX ZIP** (`.zip`)  
  The ZIP should include `.tex` files. The main file is detected by `\begin{document}`.

## 🔌 API Endpoints

- `POST /api/upload` — upload a file and parse it
- `POST /api/check` — run selected checks
- `GET /get-text?path=...` — fetch extracted text by path

## ⚠️ Disclaimer

This tool is intended for pre-submission checks only and does not guarantee full compliance with any specific conference or journal double-blind policy.

## 📝 Examples
- model: deepseek-chat
- all sources can be found in `/uploads`
 
|  |  |
|------------|----------|
|![](figs/file.png) | ![](figs/image.png) |
|![](figs/link.png) | ![](figs/cross.png) |
|![](figs/metadata.png) | ![](figs/anonymous.png) |
|![](figs/hidden.png) | ![](figs/summary.png) |

![](figs/view.png)