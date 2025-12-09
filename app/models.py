
from pydantic import BaseModel
from typing import Dict

class StatsResponse(BaseModel):
    username: str
    cached: bool
    total_bytes: Dict[str, int]
    percentages: Dict[str, float]
