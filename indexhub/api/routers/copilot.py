import asyncio
from datetime import datetime
from fastapi import APIRouter, WebSocket
import websockets
from pydantic import BaseModel
from indexhub.api.models.copilot import ForecastAnalystAgentModel
import logging
import modal.aio
import traceback

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
    policy_id: str
    target_col: str
    entity_col: str
    entity_id: str
    freq: str
    fh: int
    cutoff: datetime


@router.websocket("/copilot/ws")
async def modal_websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        logger.info("Websocket connection established.")
        params = await websocket.receive_json()
        forecast_params = ForecastParams(**params)

        get_agent = await modal.aio.AioFunction.lookup(MODAL_APP, "get_agent")
        get_analysis = await modal.aio.AioFunction.lookup(MODAL_APP, "get_analysis")
        get_questions = await modal.aio.AioFunction.lookup(MODAL_APP, "get_questions")
        get_news = await modal.aio.AioFunction.lookup(MODAL_APP, "get_news")
        get_sources = await modal.aio.AioFunction.lookup(MODAL_APP, "get_sources")
        get_one_answer = await modal.aio.AioFunction.lookup(MODAL_APP, "get_one_answer")
        logger.info(f"Modal functions loaded from {MODAL_APP}.")

        agent_params = await get_agent.call(
            forecast_params.user_id,
            forecast_params.policy_id,
            forecast_params.target_col,
            forecast_params.entity_col,
            forecast_params.entity_id,
            forecast_params.freq,
            forecast_params.fh,
            forecast_params.cutoff,
            n_iter=0,
        )
        agent = ForecastAnalystAgentModel.parse_obj(agent_params)
        logger.info("ForecastAnalystAgent initialized.")
        logger.debug(f"ForecastAnalystAgent __dict__:\n\n{agent.__dict__}")

        # TODO: This isn't used ATM
        context = ""

        async def _analysis_and_questions(agent):
            logger.info("Getting analysis")
            analysis = await get_analysis.call(agent.dict())
            await websocket.send_json({"analysis": analysis})
            logger.info("Done getting analysis")
            logger.info("Getting questions")
            questions = await get_questions.call(agent.dict(), analysis)
            await websocket.send_json({"questions": questions})
            logger.info("Done getting questions")
            return analysis, questions

        async def _news(agent):
            logger.info("Getting news")
            news = await get_news.call(agent.dict())
            await websocket.send_json({"news": news.to_dicts()})
            logger.info("Done getting news")
            return news

        async def _sources(agent):
            logger.info("Getting sources")
            sources = await get_sources.call(agent.dict())
            await websocket.send_json({"sources": sources.to_dicts()})
            logger.info("Done getting sources")
            return sources

        analysis_and_questions_task = asyncio.create_task(
            _analysis_and_questions(agent)
        )
        news_task = asyncio.create_task(_news(agent))
        sources_task = asyncio.create_task(_sources(agent))
        logger.info("Waiting for tasks")
        await asyncio.wait(
            [analysis_and_questions_task, news_task, sources_task],
            return_when=asyncio.ALL_COMPLETED,
        )
        analysis, questions = analysis_and_questions_task.result()
        news = news_task.result()
        sources = sources_task.result()

        logger.info("Questions, news, sources done")
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
    except modal.exception.NotFoundError as e:
        logger.error(f"{e}: {traceback.format_exc()}")
    except websockets.exceptions.ConnectionClosedOK as e:
        logger.info(f"Connection closed: {e}")
    except Exception as e:
        logger.error(f"{e}: {traceback.format_exc()}")
    finally:
        logger.info("Closing websocket connection.")
        await websocket.close(code=1000, reason="Connection closed.")

