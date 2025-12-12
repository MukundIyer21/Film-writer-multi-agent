from typing import TypedDict,Optional
class FilmProductionState(TypedDict):
    topic: str
    research_findings: str
    script: str
    rating: int
    feedback : Optional[str]