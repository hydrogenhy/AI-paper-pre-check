from flask import Blueprint, request, jsonify
from app.services.ingest import save_upload
from app.services.pdf_parser import parse_pdf
from app.services.latex_parser import parse_latex_zip
import os


def register_routes(app):
    bp = Blueprint("api", __name__, url_prefix="/api")

    @bp.route("/upload", methods=["POST"])
    def upload_file():
        if "file" not in request.files:
            return jsonify({"error": "no file provided"}), 400

        file = request.files["file"]
        layout = request.form.get("layout", "single")  # Get layout choice from form
        filename = file.filename or ""
        lower_name = filename.lower()
        if not (lower_name.endswith(".pdf") or lower_name.endswith(".zip")):
            return jsonify({"error": "unsupported file type: only .pdf or .zip allowed"}), 400
        try:
            path, filename = save_upload(file)
        except ValueError as e:
            return jsonify({"error": str(e)}), 413
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        # If PDF or LaTeX zip, run parser and save process outputs
        lower = filename.lower()
        if lower.endswith('.pdf'):
            try:
                process_dir, summary = parse_pdf(path, filename, layout_type=layout)
            except Exception as e:
                process_dir, summary = None, {"error": str(e)}
        elif lower.endswith('.zip'):
            try:
                process_dir, summary = parse_latex_zip(path, filename)
            except Exception as e:
                process_dir, summary = None, {"error": str(e)}
        else:
            process_dir, summary = None, None

        # Build response with parse/extraction info
        report = {"filename": filename}
        
        # attach process info when available
        if process_dir:
            # make process_dir path relative to project root for readability
            proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            try:
                rel = os.path.relpath(process_dir, proj_root)
            except Exception:
                rel = process_dir
            report["process_dir"] = rel
            
            # Add full_text path for frontend to read and run checks
            if summary and "full_text" in summary:
                report["full_text"] = summary["full_text"]

        return jsonify(report)

    app.register_blueprint(bp)
