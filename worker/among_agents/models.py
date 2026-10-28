from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Sensors(StrictModel):
    emf_milligauss: float = Field(ge=0)
    temp_c: float
    motion_events: int = Field(ge=0)


class Sighting(StrictModel):
    entity_class: str = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    witness_count: int = Field(ge=0)


class Sector(StrictModel):
    sector: str = Field(min_length=1, max_length=200)
    sensors: Sensors
    sighting: Sighting | None = None
    civilian_status: str = Field(min_length=1, max_length=300)
    containment_state: str = Field(min_length=1, max_length=100)


class Budget(StrictModel):
    max_active_agents: int = Field(ge=0)
    api_credits_remaining: int = Field(ge=0)


class Escalation(StrictModel):
    app: Literal["discord"]
    channel: str
    via: str


class Tick(StrictModel):
    tick_id: int = Field(gt=0)
    facility_id: str = Field(min_length=1, max_length=200)
    sector_reports: list[Sector] = Field(min_length=1, max_length=100)
    swarm_budget: Budget
    escalation_channel: Escalation


class Decision(StrictModel):
    action: Literal["contain", "evacuate", "observe"]
    rationale: str = Field(min_length=8, max_length=1500)
    evidence: list[str] = Field(min_length=1, max_length=12)


class AgentSummary(StrictModel):
    role: str
    summary: str


class Effect(StrictModel):
    status: str
    detail: str | None = None


class Run(StrictModel):
    id: str
    mode: Literal["demo", "live"]
    created_at: str
    tick: Tick
    decision: Decision
    agents: list[AgentSummary]
    submission: Effect
    dispatch: Effect


class RunRequest(StrictModel):
    fixture: Literal["outbreak", "control"] = "outbreak"
