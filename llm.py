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
        description="A human-readable description of what the project does"
    )
    technologies: list[str] = Field(
        description="List of main technologies, languages, and frameworks used and observed in the repo"
    )
    structure: str = Field(description="Brief description of the project structure")


SCHEMA = RepoSummary.model_json_schema()


SYSTEM_PROMPT = f"""
You analyze software repositories.
Use ONLY the provided repository profile and file excerpts.
Produce a concise architecture + tech summary.
Required information schema: {SCHEMA}
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


def reduce_key_files_content(repo_profile, max_chars):
    while len(json.dumps(repo_profile)) > max_chars and repo_profile["key_files"]:
        repo_profile["key_files"].popitem()

    if len(json.dumps(repo_profile)) > max_chars:
        # failsafe: truncate the repo profile to fit into the max chars limit
        repo_profile = str(repo_profile)[:max_chars]

    return repo_profile


def summarize_repo_with_retries(
    client, repo_profile, max_retries=5, model=MODEL, max_chars=MAX_CHARS
) -> RepoSummary:
    last_error = None
    for _ in range(max_retries):
        try:
            result = summarize_repo(client, repo_profile, model=model)
            return result
        except openai.BadRequestError as e:
            last_error = e
            if "Please reduce the length of the input messages" in e.response.text:
                print("Input too long, trying to reduce the size of files content...")
                max_chars = max_chars * CHARS_REDUCE_STEP
                repo_profile = reduce_key_files_content(repo_profile, max_chars)
            else:
                print(f"Error during summarization: {e}")
        except Exception as e:
            print(f"Error during summarization: {e}")
            last_error = e
    raise last_error
