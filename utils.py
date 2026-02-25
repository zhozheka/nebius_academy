import subprocess


def download_repo(github_url: str, clone_path: str, timeout_sec: int = 300) -> str:
    cmd = ["git", "clone", github_url, clone_path]

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_sec,
        )

    except FileNotFoundError as e:
        raise RuntimeError("git is not installed or not on PATH.") from e

    except subprocess.TimeoutExpired as e:
        raise RuntimeError("git clone timed out.") from e

    except subprocess.CalledProcessError as e:
        msg = (e.stderr or e.stdout or "").strip()
        raise RuntimeError(
            f"git clone failed: {msg if msg else 'unknown error'}"
        ) from e

    return clone_path
