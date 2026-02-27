import os
import shutil
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests


def download_repo(github_url: str, clone_path: str) -> tuple[str, str]:
    u = urlparse(github_url.strip())
    parts = [p for p in u.path.split("/") if p]
    if u.netloc.lower() not in ("github.com", "www.github.com") or len(parts) != 2:
        raise ValueError("github_url must look like https://github.com/OWNER/REPO")

    owner, repo = parts[0], parts[1].removesuffix(".git")

    out_dir = Path(clone_path).expanduser().resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError("clone_path must be an empty directory (or not exist).")
    out_dir.mkdir(parents=True, exist_ok=True)

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "simple-repo-downloader",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"

    zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"

    zip_path = Path(clone_path) / "repo.zip"
    extract_root = Path(clone_path)

    # Download (follows GitHub redirect)
    attempts = 3
    for _ in range(attempts):
        try:
            r = requests.get(
                zip_url, headers=headers, stream=True, allow_redirects=True, timeout=300
            )
            if r.status_code == 200:
                break

        except Exception:
            continue
    else:
        raise RuntimeError("Failed to download repository after multiple attempts.")

    if r.status_code != 200:
        raise RuntimeError(f"Download failed ({r.status_code}): {r.text[:300]}")
    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    # Extract
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_root)
    zip_path.unlink()

    # GitHub zipball usually has one top-level folder; copy its contents into out_dir
    top = next(extract_root.iterdir())
    if not top.is_dir():
        raise RuntimeError("Unexpected archive layout.")
    for item in top.iterdir():
        dest = out_dir / item.name
        if dest.exists():
            raise ValueError(f"Destination already contains: {dest}")
        shutil.move(str(item), str(dest))
    top.rmdir()

    return owner, repo
