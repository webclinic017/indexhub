from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import polars as pl


class Persona(BaseModel):
    identity: str
    audience: str


class Company(BaseModel):
    name: str
    description: str
    industries: list[str]
    markets: list[str]


class ForecastContextInputs(BaseModel):
    agent: Persona
    company: Company
    entity_col: str
    target_col: str
    entity_id: str
    freq: str
    fh: str
    cutoff: datetime
    forecast: pl.DataFrame
    quantiles: pl.DataFrame

    class Config:
        arbitrary_types_allowed = True


class ForecastAnalystAgentModel(BaseModel):
    context_inputs: ForecastContextInputs
    hints: Optional[List[str]]
    n_questions: Optional[int]
    n_queries: Optional[int]
    n_results: Optional[int]
    domains: Optional[List[str]]
    date_from: Optional[datetime]
    date_to: Optional[datetime]
    n_iter: int
