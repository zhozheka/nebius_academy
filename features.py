import os
from glob import glob


def get_readme_files(repo_path: str) -> dict:
    readme_file_paths = glob(os.path.join(repo_path, "**/README.md"), recursive=True)
    readme_files = {}
    for path in readme_file_paths:
        with open(path) as f:
            path = path.split(repo_path)[1]
            readme_files[path] = f.read()
    return readme_files


def get_tld_files(repo_path: str) -> list:
    top_level_directory_files = os.listdir(repo_path)
    return top_level_directory_files


def extract_repo_profile(repo_path: str) -> dict:
    repo_profile = {
        "readme_files": get_readme_files(repo_path),
        "tld_files": get_tld_files(repo_path),
    }
    return repo_profile
