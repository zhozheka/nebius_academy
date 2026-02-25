import json
import os

from openai import OpenAI
from pydantic import BaseModel, Field


class RepoSummary(BaseModel):
    summary: str = Field(
        description="A human-readable description of what the project does"
    )
    technologies: list[str] = Field(
        description="List of main technologies, languages, and frameworks used"
    )
    structure: str = Field(description="Brief description of the project structure")


schema = RepoSummary.model_json_schema()


system_prompt = f"""
You are given a Repo Profile; produce a concise architecture + tech summary,
Required information schema: {schema}
""".strip()


def get_client():
    api_key = os.environ.get("NEBIUS_API_KEY")
    if not api_key:
        raise ValueError("NEBIUS_API_KEY environment variable is not set.")

    client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/", api_key=api_key)
    return client


def summarize_repo(
    client: OpenAI, repo_profile: dict, model: str = "google/gemma-2-2b-it"
) -> RepoSummary:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(repo_profile)},
        ],
        extra_body={
            "guided_json": schema,
        },
        # temperature=0.6,
        # max_tokens=51,
        # top_p=0.9
    )

    response = RepoSummary(**json.loads(completion.choices[0].message.content))
    return response
