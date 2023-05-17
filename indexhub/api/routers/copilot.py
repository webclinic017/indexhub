import asyncio
import json
import logging
import traceback
from datetime import datetime
from functools import partial

import modal.aio
import polars as pl
import websockets
from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel
from sqlmodel import Session

from indexhub.api.db import engine
from indexhub.api.models.copilot import (
    Company,
    ForecastAnalystAgent,
    ForecastContextInputs,
    Persona,
)
from indexhub.api.models.user import User
from indexhub.api.routers.objectives import get_objective
from indexhub.api.services.io import SOURCE_TAG_TO_READER
from indexhub.api.services.secrets_manager import get_aws_secret

router = APIRouter()


def _logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(levelname)s: %(asctime)s: %(name)s  %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False  # Prevent the modal client from double-logging.
    return logger


logger = _logger(name=__name__)


MODAL_APP = "copilot-forecast-analyst-async-gpt3.5"


class ForecastParams(BaseModel):
    user_id: str
    objective_id: str
    target_col: str
    entity_col: str
    entity_id: str
    freq: str
    fh: int
    cutoff: datetime


def _get_context_inputs(params: ForecastParams) -> ForecastContextInputs:
    # Load forecast and quantiles data
    with Session(engine) as session:
        user = session.get(User, params.user_id)
        if user is None:
            raise HTTPException(
                status_code=404, detail=f"User with ID {params.user_id} not found."
            )

    objective = get_objective(params.objective_id)["objective"]
    outputs = json.loads(objective.outputs)

    storage_creds = get_aws_secret(
        tag=user.storage_tag, secret_type="storage", user_id=user.id
    )
    read = partial(
        SOURCE_TAG_TO_READER[user.storage_tag],
        bucket_name=user.storage_bucket_name,
        **storage_creds,
    )

    forecast: pl.DataFrame = read(
        object_path=outputs["forecasts"]["best_models"], file_ext="parquet"
    ).filter(pl.col(params.entity_col) == params.entity_id)
    quantiles: pl.DataFrame = (
        read(object_path=outputs["quantiles"]["best_models"], file_ext="parquet")
        .filter(pl.col(params.entity_col) == params.entity_id)
        .filter(pl.col("quantile").is_in([10, 90]))
    )

    onboarding_data = read(
        object_path="users-context/copilot-onboarding.json", file_ext="json"
    )
    agent_persona = Persona(**onboarding_data["persona"])
    company = Company(**onboarding_data["company"])

    context_inputs = ForecastContextInputs(
        agent=agent_persona,
        company=company,
        target_col=params.target_col,
        entity_col=params.entity_col,
        entity_id=params.entity_id,
        freq=params.freq,
        fh=params.fh,
        cutoff=params.cutoff,
        forecast=forecast,
        quantiles=quantiles,
    )
    return context_inputs


async def _analysis_and_questions(
    websocket: WebSocket, agent: ForecastAnalystAgent
) -> tuple[list[str], list[str]]:
    logger.info("Getting analysis")
    get_analysis = await modal.aio.AioFunction.lookup(MODAL_APP, "get_analysis")
    analysis = await get_analysis.call(agent.dict())
    await websocket.send_json({"analysis": analysis})
    logger.info("Done getting analysis")

    logger.info("Getting questions")
    get_questions = await modal.aio.AioFunction.lookup(MODAL_APP, "get_questions")
    questions = await get_questions.call(agent.dict(), analysis)
    await websocket.send_json({"questions": questions})
    logger.info("Done getting questions")
    return analysis, questions


async def _news(websocket: WebSocket, agent: ForecastAnalystAgent) -> pl.DataFrame:
    logger.info("Getting news")
    get_news = await modal.aio.AioFunction.lookup(MODAL_APP, "get_news")
    news = await get_news.call(agent.dict())
    await websocket.send_json({"news": news.to_dicts()})
    logger.info("Done getting news")
    return news


async def _sources(websocket: WebSocket, agent: ForecastAnalystAgent) -> pl.DataFrame:
    logger.info("Getting sources")
    get_sources = await modal.aio.AioFunction.lookup(MODAL_APP, "get_sources")
    sources = await get_sources.call(agent.dict())
    await websocket.send_json({"sources": sources.to_dicts()})
    logger.info("Done getting sources")
    return sources


async def _answer(
    websocket: WebSocket,
    agent: ForecastAnalystAgent,
    context: str,
    analysis: list[str],
    questions: list[str],
    sources: pl.DataFrame,
    news: pl.DataFrame,
):
    get_one_answer = await modal.aio.AioFunction.lookup(MODAL_APP, "get_one_answer")
    tasks = [
        get_one_answer.call(
            agent_params=agent.dict(),
            context=context,
            analysis=analysis,
            question=question,
            sources=sources,
            news=news,
        )
        for question in questions
    ]
    n_parts = len(tasks)
    logger.info(f"Answering {n_parts} questions")
    for i, future in enumerate(asyncio.as_completed(tasks)):
        q, a = await future
        payload = {"q": q, "a": a, "part": i + 1, "n_parts": n_parts}
        await websocket.send_json({"answer": payload})
        logger.info(f"Answered question {i+1} of {n_parts}")


@router.websocket("/copilot/ws")
async def generate_forecastgpt_report(websocket: WebSocket):
    try:
        await websocket.accept()
        logger.info("Websocket connection established.")
        ws_params = await websocket.receive_json()
        params = ForecastParams(**ws_params)
        logger.info(f"Received forecast params: {params}")

        context_inputs = _get_context_inputs(params)
        logger.info("Got context inputs.")

        agent = ForecastAnalystAgent(context_inputs=context_inputs, n_iter=0)

        logger.info("ForecastAnalystAgent initialized.")
        logger.info(f"ForecastAnalystAgent __dict__:\n\n{agent.__dict__}")

        # TODO: Decide whether to pass in context or not
        context = ""

        analysis_and_questions_task = asyncio.create_task(
            _analysis_and_questions(websocket, agent)
        )
        news_task = asyncio.create_task(_news(websocket, agent))
        sources_task = asyncio.create_task(_sources(websocket, agent))
        logger.info("Waiting for tasks")
        await asyncio.wait(
            [analysis_and_questions_task, news_task, sources_task],
            return_when=asyncio.ALL_COMPLETED,
        )
        analysis, questions = analysis_and_questions_task.result()
        news = news_task.result()
        sources = sources_task.result()

        logger.info("Questions, news, sources done")
        await _answer(
            websocket,
            agent,
            context,
            analysis,
            questions,
            sources,
            news,
        )

    except modal.exception.NotFoundError as e:
        logger.error(f"{e}: {traceback.format_exc()}")
    except websockets.exceptions.ConnectionClosedOK as e:
        logger.info(f"Connection closed: {e}")
    except Exception as e:
        logger.error(f"{e}: {traceback.format_exc()}")
    finally:
        logger.info("Closing websocket connection.")
        await websocket.close(code=1000, reason="Connection closed.")
