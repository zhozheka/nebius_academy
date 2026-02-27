import fnmatch
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from llm import MAX_CHARS
from rules import (
    BASE_PRIORITY,
    BINARY_EXTS,
    DECAY_PER_DEPTH,
    DEFAULT_IGNORE_DIRS,
    KEY_FILE_RULES,
    LOCKFILE_NAMES,
    MAX_CHARS_PER_FILE,
    MAX_PRIORITY,
)

MAX_CHARS_PER_FILE


@dataclass(frozen=True)
class KeyFile:
    relpath: str
    abspath: Path
    priority: int


def _sniff_is_binary(p: Path, sniff_bytes: int = 2048) -> bool:
    try:
        with p.open("rb") as f:
            chunk = f.read(sniff_bytes)
        return b"\x00" in chunk
    except Exception:
        return True


def _match_any(relpath: str, patterns: Iterable[str]) -> bool:
    rel = relpath.lower()
    base = Path(relpath).name.lower()
    for pat in patterns:
        p = pat.lower()
        if fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(base, p):
            return True
    return False


def get_files_with_priority(
    repo_path: str, decay_readme: bool = True, max_readmes: int = 20
) -> list[KeyFile]:
    n_readmes = 0
    root = Path(repo_path).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"repo_path is not a directory: {repo_path}")

    files = []

    for dirpath, dirnames, filenames in os.walk(root):
        if Path(dirpath).name in DEFAULT_IGNORE_DIRS:
            continue
        depth = len(Path(dirpath).relative_to(root).parts)

        for fn in filenames:
            if fn in LOCKFILE_NAMES:
                continue

            p = Path(dirpath) / fn

            # skip binary files
            if p.suffix.lower() in BINARY_EXTS or _sniff_is_binary(p):
                continue

            if fn == "readme" or fn.startswith("readme.") and decay_readme:
                n_readmes += 1
                if n_readmes > max_readmes:
                    priority = BASE_PRIORITY - depth * DECAY_PER_DEPTH
                else:
                    priority = (
                        MAX_PRIORITY - depth * 25
                    )  # decay readme priority by depth
                files.append(
                    KeyFile(
                        relpath=str(Path(dirpath).relative_to(root) / fn),
                        abspath=Path(dirpath) / fn,
                        priority=priority,
                    )
                )
                continue

            p = Path(dirpath) / fn
            try:
                rel = p.relative_to(root).as_posix()
            except Exception:
                continue

            priority = BASE_PRIORITY
            for priority_, patterns in KEY_FILE_RULES:
                if _match_any(rel, patterns):
                    priority = priority_ - depth * DECAY_PER_DEPTH
                    break

            files.append(KeyFile(relpath=rel, abspath=p, priority=priority))
    return sorted(files, key=lambda k: (-k.priority, k.relpath.lower()))


def get_extension_counter(
    files: list[KeyFile], prune: bool = True
) -> dict[str, dict[str, int]]:
    def _count_loc(p: Path) -> int:
        try:
            with p.open("r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0

    extension_counter = defaultdict(lambda: {"files": 0, "loc": 0})

    for kf in files:
        p = kf.abspath

        ext = p.suffix  # keeps leading dot; empty string for no suffix
        extension_counter[ext]["files"] += 1
        extension_counter[ext]["loc"] += _count_loc(p)
    if prune:
        # Remove extensions that only appear once and have very few lines of code (likely not significant for repo profile)
        extension_counter = dict(
            (ext, data)
            for ext, data in extension_counter.items()
            if data["files"] > 5 and data["loc"] > 0
        )
    return extension_counter


def get_top_level_directories(repo_dir):
    tlds = []
    for f in Path(repo_dir).iterdir():
        if f.is_dir():
            tlds.append(
                {"name": f.name, "n_files": sum(1 for _ in f.rglob("*") if _.is_file())}
            )
        else:
            tlds.append(
                {
                    "name": f.name,
                }
            )
    return tlds


def pack_key_files_content(repo_profile, files):
    files_budget = MAX_CHARS - len(json.dumps(repo_profile))
    key_files_content = {}
    while files_budget > 0 and files:
        kf = files.pop(0)
        try:
            content = kf.abspath.read_text(encoding="utf-8", errors="ignore")[
                :MAX_CHARS_PER_FILE
            ]
        except Exception:
            continue

        new_file_budget = (
            len(content) + len(kf.relpath) + 100
        )  # add some overhead for formatting
        if new_file_budget > files_budget:
            break
        key_files_content[kf.relpath] = content
        files_budget -= new_file_budget

    repo_profile["key_files"] = key_files_content
    return repo_profile


def build_repo_profile(repo_dir: str) -> dict:
    files = get_files_with_priority(repo_dir, decay_readme=True, max_readmes=20)
    extension_counter = get_extension_counter(files)
    top_level_directories = get_top_level_directories(repo_dir)

    repo_profile = {
        "repo_name": Path(repo_dir).name,
        "top_level_directories": top_level_directories,
        "num_files": len(files),
        "extensions": extension_counter,
    }
    repo_profile = pack_key_files_content(repo_profile, files)
    return repo_profile
