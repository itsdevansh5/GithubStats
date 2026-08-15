
from pydantic import BaseModel,StringConstraints
from typing import Dict,Annotated


class StatsResponse(BaseModel):
    username: str
    cached: bool
    total_bytes: Dict[str, int]
    percentages: Dict[str, float]

GithubUsername = Annotated[str,
                          StringConstraints(pattern=r"[A-Za-z0-9-]{1,39}")
]

