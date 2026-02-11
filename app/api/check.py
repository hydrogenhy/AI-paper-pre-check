import os
import json
from flask import request, jsonify
from app.checks import run_checks
from app.api.log_praser import parse_check_log


def check_text():
    """Run checks on extracted PDF text.
    
    Expected request format:
    {
        "text": "full extracted text from PDF",
        "filename": "original_filename",
        "process_dir": "path to process directory"
    }
    """
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' field"}), 400
        
        text = data["text"]
        filename = data.get("filename", "unknown")
        filename = filename.replace(" ", "_")
        process_dir = data.get("process_dir", None)
        enabled_checks = data.get("checks", None)
        if enabled_checks is not None and not isinstance(enabled_checks, list):
            return jsonify({"error": "'checks' must be a list"}), 400
        
        if not text or not isinstance(text, str):
            return jsonify({"error": "'text' must be a non-empty string"}), 400
        
        # Convert relative path to absolute if needed
        if process_dir and not os.path.isabs(process_dir):
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            process_dir = os.path.join(root, process_dir)
            process_dir = os.path.normpath(process_dir)
            file_path = os.path.join(os.path.dirname(os.path.dirname(process_dir)), filename)
        
        results = run_checks(
            file_path=file_path,
            proj_path=process_dir,
            filename=filename,
            text=text,
            enabled_checks=enabled_checks,
        )
        parsed = parse_check_log(
            results,
            context={
                "process_dir": process_dir,
                "file_path": file_path,
            },
        )
        
        return jsonify(parsed), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_text():
    """Retrieve text content from a file path.
    
    Query params:
        path: Full path to text file
    """
    try:
        file_path = request.args.get('path', '')
        
        if not file_path:
            return jsonify({"error": "Missing 'path' parameter"}), 400
        
        if not os.path.exists(file_path):
            return jsonify({"error": f"File not found: {file_path}"}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def register_check_routes(app):
    """Register check-related routes with Flask app.
    
    Args:
        app: Flask application instance
    """
    app.add_url_rule(
        "/api/check",
        "check_text",
        check_text,
        methods=["POST"]
    )
    
    app.add_url_rule(
        "/get-text",
        "get_text",
        get_text,
        methods=["GET"]
    )
