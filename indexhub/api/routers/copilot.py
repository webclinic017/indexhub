import asyncio
import json
import logging
import traceback
from datetime import datetime
from functools import partial
from typing import List, Optional
from collections import deque

import modal
import polars as pl
import websockets
from fastapi import HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlmodel import Session

from indexhub.api.db import create_sql_engine
from indexhub.api.demos import DEMO_BUCKET, DEMO_SCHEMAS
from indexhub.api.models.copilot import (
    Action,
    AdditionalType,
    Company,
    ForecastAnalystAgent,
    ForecastContextInputs,
    Persona,
    ChatMessage,
    Request,
)
from indexhub.api.models.user import User
from indexhub.api.routers import router
from indexhub.api.routers.objectives import get_objective
from indexhub.api.routers.trends import (
    _create_trend_chart,
    _create_trend_data,
    _load_trend_datasets,
)
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
    engine = create_sql_engine()
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
    action: Action,
    additional_type: Optional[AdditionalType] = None,
    **kwargs,
) -> Request:
    return Request(
        role="assistant",
        action=action,
        additional_type=additional_type,
        channel=0,
        props={
            **kwargs,
        },
        content=content,
    )


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
            case "describe":
                logger.info("Describing")
                await self.describe(msg)
            case "report_flow":
                logger.info("Reporting flow")
                await self.report_flow(msg)
            case "sentiment_analysis":
                logger.info("Sentiment analysis")
                await self.sentiment_analysis(msg)
            case _:
                logger.error(f"Unknown action: {action}")

    # NOTE: This is the old analysis. Keeping for backwards compatibility
    async def _analysis(self, msg: ChatMessage) -> tuple[list[str], list[str]]:
        logger.info("Getting analysis")
        get_analysis = modal.Function.lookup(MODAL_APP, "get_analysis")
        analysis = await get_analysis.call.aio(self.agent.dict())
        await self.websocket.send_json(
            {"analysis": analysis, "channel": msg.request.channel}
        )
        logger.info("Done getting analysis")
        return analysis

    async def _questions(
        self, msg: ChatMessage, analysis: list[str]
    ) -> tuple[list[str], list[str]]:
        logger.info("Getting questions")
        get_questions = modal.Function.lookup(MODAL_APP, "get_questions")
        questions = await get_questions.call.aio(self.agent.dict(), analysis)
        await self.websocket.send_json(
            {"questions": questions, "channel": msg.request.channel}
        )
        logger.info("Done getting questions")
        return questions

    async def _news(self, msg: ChatMessage) -> pl.DataFrame:
        logger.info("Getting news")
        get_news = modal.Function.lookup(MODAL_APP, "get_news")
        news = await get_news.call.aio(self.agent.dict())
        await self.websocket.send_json(
            {"news": news.to_dicts(), "channel": msg.request.channel}
        )
        logger.info("Done getting news")
        return news

    async def _sources(self, msg: ChatMessage) -> pl.DataFrame:
        logger.info("Getting sources")
        get_sources = modal.Function.lookup(MODAL_APP, "get_sources")
        sources = await get_sources.call.aio(self.agent.dict())
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
        get_one_answer = modal.Function.lookup(MODAL_APP, "get_one_answer")
        tasks = [
            get_one_answer.call.aio(
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
        get_chat = modal.Function.lookup(MODAL_APP, "get_chat_response")
        response = await get_chat.call.aio(
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
        get_sentiment = modal.Function.lookup(MODAL_APP, "get_sentiment")
        response = await get_sentiment.call.aio(agent_params=self.agent.dict())
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
async def forecast_analyst_chat(websocket: WebSocket):
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


class TrendsChatContext(BaseModel):
    dataset_id: str
    entity_id: str
    entity_col: str
    target_col: str
    forecasts: pl.DataFrame
    quantiles: pl.DataFrame
    chart: str

    class Config:
        arbitrary_types_allowed = True


class TrendsChatService:
    def __init__(
        self,
        websocket: WebSocket,
        user_id: str,
        max_context_length: int = 2,
        max_message_history: int = 50,
    ):
        self.user_id = user_id
        self.websocket = websocket
        self.max_message_history = max_message_history
        # self.messages = deque(maxlen=50)  # Chat history maintained on FE
        self.context = deque(maxlen=max_context_length)  # Data it's looking at
        self.reader = partial(
            SOURCE_TAG_TO_READER["s3"],
            bucket_name=DEMO_BUCKET,
            file_ext="parquet",
        )

    @property
    def name(self):
        return "IndexBot"

    async def dispatch(self, msg: ChatMessage):
        # We should never hit a mismatched action as pydantic validates the input
        action = msg.request.action
        match action:
            case "chat":
                await self.chat(msg)
            case "load_context":
                await self.load_context(msg)
            case _:
                logger.error(f"Unknown action: {action}")

    async def load_context(self, msg: ChatMessage):
        """Load trend context after selecting an embedding.

        We pass in the context from the FE through the props variable in the request.
        This should contain dataset_id, entity_id required to make the call.

        """
        logger.info("Loading context")

        dataset_id = msg.request.props["dataset_id"]
        entity_id = msg.request.props["entity_id"]

        # Get tables and chart
        paths = DEMO_SCHEMAS[dataset_id]
        trend_datasets = _load_trend_datasets(self.reader, paths)
        actual, forecasts, quantiles, _ = trend_datasets
        entity_col, _, target_col = actual.columns
        chart_data = _create_trend_data(
            *trend_datasets,
            entity_id=entity_id,
        )

        forecasts = forecasts.filter(pl.col(entity_col) == entity_id)
        quantiles = quantiles.filter(pl.col(entity_col) == entity_id).filter(
            pl.col("quantile").is_in([10, 90])
        )
        # Create chart - this needs to be handled separately
        chart = _create_trend_chart(chart_data).to_json()
        new_context = TrendsChatContext(
            dataset_id=dataset_id,
            entity_id=entity_id,
            entity_col=entity_col,
            target_col=target_col,
            forecasts=forecasts,
            quantiles=quantiles,
            chart=chart,
        )
        self.context.append(new_context)
        msg_content = (
            f"I've loaded the context for {dataset_id}:{entity_id}!"
            f" My context now contains {[f'{ctx.dataset_id}:{ctx.entity_id}' for ctx in self.context]}."
        )
        logger.info(f"{msg_content}")
        chat_response = format_chat_response(
            content=msg_content,
            action=msg.request.action,
            additional_type="chart",
            chart=chart,
        )
        await self.websocket.send_json(
            {"response": chat_response.dict(), "channel": msg.request.channel}
        )

    def _get_context_block(self):
        if not self.context:
            return "You do not have any context loaded."
        contexts = []
        for ctx in self.context:
            section = (
                f"## {ctx.dataset_id} - {ctx.entity_id}"
                f"\n\n{ctx.forecasts.to_pandas().to_markdown(index=False)}"
                f"\n\n{ctx.quantiles.to_pandas().to_markdown(index=False)}"
            )
            contexts.append(section)
        return "\n\n".join(contexts)

    def _format_messages(self, msg: ChatMessage):
        """Modify the request for the chatbot service.

        This step involves creating the prompt for the agent.chat endpoint.

        """
        system_message = {
            "role": "system",
            "content": (
                f"You are an AI chatbot called {self.name}."
                " You are an expert forecast analyst and data communicator."
                " You always speak clearly and concisely."
                " You use simple percentage and difference calculations to explain trends."
                " You do not answer questions you do not know the answer to."
                " If you don't know the answer to a question, say that you don't know, and don't make up answers."
                " You do not provide recommendations that you could put."
                " You are having a conversation with a user."
                " Your job is to answer questions about forecast trends to the best of your ability."
            ),
        }
        curr_date = datetime.now().strftime("%B %Y")
        prompt = (
            "These are the datasets you are currently looking at:"
            f"\n\n```{self._get_context_block()}```"
            "\n\nUse the above data, general knowledge, and expert reasoning ability to respond to the user's message."
            f" Note that it is now {curr_date} - COVID-19 is no longer relevant."
            " Be specific and respond with non-obvious statistical analysis."
            " Describe trend, seasonality, and anomalies. Do not provide recommendations. Do not describe or refer to the table."
            f"\nUser: {msg.request.content}"
            f"\n\n{self.name}:"
        )

        user_message = {"role": "user", "content": prompt}
        messages = [
            system_message,
            *msg.message_history[: self.max_message_history],
            user_message,
        ]
        return messages

    async def chat(
        self, msg: ChatMessage, model: str = "gpt-3.5-turbo", temperature: float = 0.5
    ):
        logger.info("Chatting")
        # Using modal endpoint that does a raw openai call for maximum flexibility
        get_raw_chat_response = modal.Function.lookup(
            MODAL_APP, "get_raw_chat_response"
        )
        messages = self._format_messages(msg)
        response = await get_raw_chat_response.call.aio(
            messages=messages, model=model, temperature=temperature
        )
        chat_response = format_chat_response(
            content=response,
            action=msg.request.action,
        )
        logger.info(f"{response}")
        await self.websocket.send_json(
            {"response": chat_response.dict(), "channel": msg.request.channel}
        )


@router.websocket("/trends/copilot/ws")
async def trends_analyst_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info("Websocket connection established.")
    config = await websocket.receive_json()
    logger.info(f"Hello user {config['user_id']}.")
    copilot = TrendsChatService(websocket, **config)
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
