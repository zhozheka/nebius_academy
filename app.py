from __future__ import annotations

import re
import tempfile
from typing import Any, Dict

from flask import Flask, jsonify, request

from features import extract_repo_profile
from llm import get_client, summarize_repo
from utils import download_repo

app = Flask(__name__)
client = get_client()


# Simple GitHub URL validator: supports https://github.com/OWNER/REPO (optional .git, optional trailing slash)
GITHUB_REPO_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


def error_response(message: str, status_code: int = 400):
    return jsonify({"status": "error", "message": message}), status_code


def process_repo(github_url: str) -> Dict[str, Any]:
    client = get_client()

    with tempfile.TemporaryDirectory() as tmp_repo_dir:
        download_repo(github_url, tmp_repo_dir)
        repo_profile = extract_repo_profile(tmp_repo_dir)

    print(repo_profile)
    repo_summary = summarize_repo(client, repo_profile)
    return repo_summary.model_dump_json()


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

    if not GITHUB_REPO_URL_RE.match(github_url.strip()):
        return error_response(
            "github_url must be a valid GitHub repository URL like https://github.com/owner/repo",
            400,
        )

    try:
        result = process_repo(github_url)
    except ValueError as e:
        return error_response(str(e), 400)

    except Exception as e:
        return error_response(
            f"An error occurred while processing the repository: {str(e)}", 500
        )
        # return error_response("Internal server error.", 500)

    return jsonify(result), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
