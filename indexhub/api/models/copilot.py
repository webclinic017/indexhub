from datetime import datetime
from typing import Any, Dict, List, Literal, Mapping, Optional
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


class ForecastAnalystAgent(BaseModel):
    context_inputs: ForecastContextInputs
    hints: Optional[List[str]]
    n_questions: Optional[int]
    n_queries: Optional[int]
    n_results: Optional[int]
    domains: Optional[List[str]]
    date_from: Optional[datetime]
    date_to: Optional[datetime]
    n_iter: Optional[int]


AdditionalType = Literal["metric", "chart", "trend", "stream_chunk"]
Role = Literal["user", "assistant"]
Action = Literal["chat", "report_flow", "sentiment_analysis", "load_context", "stream_chat"]


class Request(BaseModel):
    role: Role
    action: Action
    additional_type: Optional[AdditionalType]
    channel: int
    props: Optional[Mapping[str, Any]]
    content: str


class ChatMessage(BaseModel):
    message_history: List[Dict[str, str]]
    request: Request
