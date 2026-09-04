
from pydantic import BaseModel,StringConstraints
from typing import Dict,Annotated


class StatsResponse(BaseModel):
    username: str
    cached: bool
    language_aggregate: Dict[str, int]
    percentages: Dict[str, float]
    total_repos: int
    total_bytes: int
    fetched_at: str

GithubUsername = Annotated[str,
                          StringConstraints(pattern=r"[A-Za-z0-9-]{1,39}")
]

