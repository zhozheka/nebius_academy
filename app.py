from __future__ import annotations

import argparse
import tempfile
from typing import Any, Dict

from flask import Flask, jsonify, request

from features import build_repo_profile
from llm import get_client, summarize_repo_with_retries
from utils import download_repo

app = Flask(__name__)
client = get_client()


def error_response(message: str, status_code: int = 400):
    return jsonify({"status": "error", "message": message}), status_code


def process_repo(github_url: str) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp_repo_dir:
        owner, repo = download_repo(github_url, tmp_repo_dir)
        repo_profile = build_repo_profile(tmp_repo_dir)
        repo_profile["owner"] = owner
        repo_profile["repo"] = repo

    repo_summary = summarize_repo_with_retries(client, repo_profile)
    return repo_summary.model_dump()


@app.post("/summarize")
def summarize_endpoint():
    if not request.is_json:
        return error_response(
            "Request must be JSON (Content-Type: application/json).", 415
        )

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("Malformed JSON body.", 400)

    github_url = data.get("github_url")
    if github_url is None:
        return error_response("Missing required field: github_url", 400)

    if not isinstance(github_url, str) or not github_url.strip():
        return error_response("github_url must be a non-empty string.", 400)

    try:
        result = process_repo(github_url.strip())
    except ValueError as e:
        return error_response(str(e), 400)

    except Exception as e:
        return error_response(
            f"An error occurred while processing the repository: {str(e)}", 500
        )

    return jsonify(result), 200


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Flask app.")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to run the app on"
    )
    parser.add_argument("--port", type=int, default=8000, help="Port to run the app on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    app.run(host=args.host, port=args.port, debug=args.debug)
