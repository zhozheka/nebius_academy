import json
import os

import openai
from pydantic import BaseModel, Field

MODEL = "Qwen/Qwen3-Coder-480B-A35B-Instruct"
MAX_TOKENS = 262144
CHARS_IN_TOKEN = 3.5  # conservative estimation based on observations
MAX_CHARS = MAX_TOKENS * CHARS_IN_TOKEN * 0.9
CHARS_REDUCE_STEP = 0.8


class RepoSummary(BaseModel):
    summary: str = Field(
        description="2–4 sentence plain-language description of what the project does: purpose, main functionality, and target users or use case. Be specific; avoid generic phrases like 'a software project'."
    )
    technologies: list[str] = Field(
        description="Ordered list of main technologies: programming languages, frameworks, runtimes, and key libraries observed in the repo (e.g. Python, React, FastAPI). Include versions only when clearly stated (e.g. Python 3.11). No duplicates; 3–15 items typical."
    )
    structure: str = Field(
        description="Short description of how the codebase is organized: main top-level directories, where application code vs config vs tests live, and any notable layout patterns. 2–5 sentences."
    )


SCHEMA = RepoSummary.model_json_schema()


SYSTEM_PROMPT = f"""
You are a precise repository analyst. Your input is a JSON "repository profile" containing:
- repo_name, top_level_directories (with file counts), extensions (file counts and lines of code), and key_files (path → excerpt).

Your task: produce a concise, accurate summary that could serve as a repository description or onboarding doc.

Instructions:
1. Base all output strictly on the provided profile. Do not invent technologies or features not evidenced by extensions, file names, or key_files content.
2. For "summary": infer purpose and main functionality from READMEs, entry points, config files, and code excerpts. Mention target users or domain when clear.
3. For "technologies": derive from extensions (e.g. .py → Python), lockfiles, config keys, and imports/requires in key_files. Prefer concrete names (e.g. "FastAPI" not just "web framework").
4. For "structure": use top_level_directories and key_files paths to describe layout (e.g. "app/ for backend, frontend/ for UI, tests/ for tests"). Note conventions (e.g. monorepo, src/ layout).

Output schema (strict JSON): {SCHEMA}
""".strip()


def get_client():
    api_key = os.environ.get("NEBIUS_API_KEY")
    if not api_key:
        raise ValueError("NEBIUS_API_KEY environment variable is not set.")

    client = openai.OpenAI(
        base_url="https://api.tokenfactory.nebius.com/v1/", api_key=api_key
    )
    return client


def summarize_repo(
    client: openai.OpenAI, repo_profile: dict, model: str
) -> RepoSummary:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(repo_profile)},
        ],
        extra_body={
            "guided_json": SCHEMA,
        },
        temperature=0.0,
        top_p=1.0,
    )

    response = RepoSummary(**json.loads(completion.choices[0].message.content))
    return response


def reduce_key_files_content(repo_profile: dict, max_chars: int) -> dict:
    while len(json.dumps(repo_profile)) > max_chars and repo_profile["key_files"]:
        repo_profile["key_files"].popitem()

    if len(json.dumps(repo_profile)) > max_chars:
        # failsafe: truncate the repo profile to fit into the max chars limit
        repo_profile = {"truncated": str(repo_profile)[:max_chars]}

    return repo_profile


def summarize_repo_with_retries(
    client: openai.OpenAI,
    repo_profile: dict,
    max_retries: int = 5,
    model: str = MODEL,
    max_chars: int = MAX_CHARS,
) -> RepoSummary:
    last_error = None
    assert max_retries > 0, "max_retries must be greater than 0"
    for _ in range(max_retries):
        try:
            result = summarize_repo(client, repo_profile, model=model)
            return result
        except openai.BadRequestError as e:
            last_error = e
            if "Please reduce the length of the input messages" in e.response.text:
                max_chars = max_chars * CHARS_REDUCE_STEP
                repo_profile = reduce_key_files_content(repo_profile, max_chars)
        except Exception as e:
            last_error = e
    raise last_error
