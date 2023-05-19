import asyncio
import json
import logging
import traceback
from datetime import datetime
from functools import partial
from typing import List, Optional

import modal.aio
import polars as pl
import websockets
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlmodel import Session

from indexhub.api.db import engine
from indexhub.api.models.copilot import (
    ACTIONS,
    ADDITIONAL_TYPES,
    Company,
    ForecastAnalystAgent,
    ForecastContextInputs,
    Persona,
    ChatMessage,
)
from indexhub.api.models.user import User
from indexhub.api.routers import router
from indexhub.api.routers.objectives import get_objective
from indexhub.api.services.io import SOURCE_TAG_TO_READER
from indexhub.api.services.secrets_manager import get_aws_secret


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


# TODO: This needs to change because we want to support browsing various time series
# and then interrogate the data. This means that the `forecast` and `quantiles` dataframes
# should be switched out on demand
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
    best_model = outputs["best_model"]
    forecast: pl.DataFrame = read(
        object_path=outputs["forecasts"][best_model], file_ext="parquet"
    ).filter(pl.col(params.entity_col) == params.entity_id)
    quantiles: pl.DataFrame = (
        read(object_path=outputs["quantiles"][best_model], file_ext="parquet")
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
    logger.info("Got context inputs.")
    return context_inputs


def format_chat_response(
    content: str,
    *,
    action: ACTIONS,
    additional_type: Optional[ADDITIONAL_TYPES] = None,
    **kwargs,
) -> dict:
    return {
        "role": "assistant",
        "action": action,
        "additional_type": additional_type,
        "props": {
            **kwargs,
        },
        "content": content,
    }


class ChatService:
    def __init__(self, websocket: WebSocket, params: ForecastParams):
        self.websocket = websocket
        self.params = params
        context_inputs = _get_context_inputs(params)
        self.agent = ForecastAnalystAgent(context_inputs=context_inputs, n_iter=0)
        logger.info("ForecastAnalystAgent initialized.")
        logger.debug(f"ForecastAnalystAgent __dict__:\n\n{self.agent.__dict__}")

    async def dispatch(self, msg: ChatMessage):
        action = msg.request.action
        match action:
            case "chat":
                logger.info("Chatting")
                await self.chat(msg)
            case "report_flow":
                logger.info("Reporting flow")
                await self.report_flow(msg)
            case "sentiment_analysis":
                logger.info("Sentiment analysis")
                await self.sentiment_analysis(msg)
            case _:
                logger.error(f"Unknown action: {action}")

    async def _analysis_and_questions(
        self, msg: ChatMessage
    ) -> tuple[list[str], list[str]]:
        logger.info("Getting analysis")
        get_analysis = await modal.aio.AioFunction.lookup(MODAL_APP, "get_analysis")
        analysis = await get_analysis.call(self.agent.dict())
        await self.websocket.send_json(
            {"analysis": analysis, "channel": msg.request.channel}
        )
        logger.info("Done getting analysis")

        logger.info("Getting questions")
        get_questions = await modal.aio.AioFunction.lookup(MODAL_APP, "get_questions")
        questions = await get_questions.call(self.agent.dict(), analysis)
        await self.websocket.send_json(
            {"questions": questions, "channel": msg.request.channel}
        )
        logger.info("Done getting questions")
        return analysis, questions

    async def _news(self, msg: ChatMessage) -> pl.DataFrame:
        logger.info("Getting news")
        get_news = await modal.aio.AioFunction.lookup(MODAL_APP, "get_news")
        news = await get_news.call(self.agent.dict())
        await self.websocket.send_json(
            {"news": news.to_dicts(), "channel": msg.request.channel}
        )
        logger.info("Done getting news")
        return news

    async def _sources(self, msg: ChatMessage) -> pl.DataFrame:
        logger.info("Getting sources")
        get_sources = await modal.aio.AioFunction.lookup(MODAL_APP, "get_sources")
        sources = await get_sources.call(self.agent.dict())
        await self.websocket.send_json(
            {"sources": sources.to_dicts(), "channel": msg.request.channel}
        )
        logger.info("Done getting sources")
        return sources

    async def _answer(
        self,
        msg: ChatMessage,
        analysis: list[str],
        questions: list[str],
        sources: pl.DataFrame,
        news: pl.DataFrame,
    ):
        get_one_answer = await modal.aio.AioFunction.lookup(MODAL_APP, "get_one_answer")
        tasks = [
            get_one_answer.call(
                agent_params=self.agent.dict(),
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
            await self.websocket.send_json(
                {"answer": payload, "channel": msg.request.channel}
            )
            logger.info(f"Answered question {i+1} of {n_parts}")

    async def report_flow(self, msg: ChatMessage):
        analysis_and_questions_task = asyncio.create_task(
            self._analysis_and_questions(msg)
        )
        news_task = asyncio.create_task(self._news(msg))
        sources_task = asyncio.create_task(self._sources(msg))
        logger.info("Waiting for tasks")
        await asyncio.wait(
            [analysis_and_questions_task, news_task, sources_task],
            return_when=asyncio.ALL_COMPLETED,
        )
        analysis, questions = analysis_and_questions_task.result()
        news = news_task.result()
        sources = sources_task.result()

        logger.info("Questions, news, sources done")
        await self._answer(
            msg,
            analysis,
            questions,
            sources,
            news,
        )

    async def chat(self, msg: ChatMessage):
        logger.info("Chatting")
        # TODO: Actually implement this logic. Placeholder for now
        get_chat = await modal.aio.AioFunction.lookup(MODAL_APP, "get_chat_response")
        response = await get_chat.call(
            agent_params=self.agent.dict(),
            message=msg.request.content,
            message_history=msg.message_history,
        )
        chat_response = format_chat_response(
            content=response,
            action=msg.request.action,
        )
        await self.websocket.send_json(
            {"chat_response": chat_response, "channel": msg.request.channel}
        )

    async def sentiment_analysis(self, msg: ChatMessage):
        logger.info("Sentiment analysis")
        get_sentiment = await modal.aio.AioFunction.lookup(MODAL_APP, "get_sentiment")
        response = await get_sentiment.call(agent_params=self.agent.dict())
        chat_response = format_chat_response(
            (
                f"Across {response['metadata']['successes']} sources the average "
                f"sentiment is {response['avg_sentiment_score']:.3f}."
                f"\n\nThe sentiment distribution is as follows:"
                f"{str(response['metadata']['sent_to_occurrence'])[1:-1].lower()}"
            ),
            action=msg.request.action,
            json_spec=response["chart_data"],
            avg_sentiment_score=response["avg_sentiment_score"],
        )
        await self.websocket.send_json(
            {"chat_response": chat_response, "channel": msg.request.channel}
        )


@router.websocket("/copilot/ws")
async def copilot_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info("Websocket connection established.")
    ws_params = await websocket.receive_json()
    params = ForecastParams(**ws_params)
    logger.info(f"Received forecast params: {params}")
    copilot = ChatService(websocket, params)

    try:
        while True:
            msg_json = await websocket.receive_json()
            msg = ChatMessage(**msg_json)
            await copilot.dispatch(msg)
    except modal.exception.NotFoundError as e:
        logger.error(f"{e}: {traceback.format_exc()}")
    except websockets.exceptions.ConnectionClosedOK as e:
        logger.info(f"Connection closed: {e}")
    except WebSocketDisconnect as e:
        logger.error(f"Connection closed: {e}")
    except Exception as e:
        logger.error(f"{e}: {traceback.format_exc()}")
    finally:
        logger.info("Closing websocket connection.")
