FROM python:3.10-slim-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY pyproject.toml pyproject.toml
COPY indexhub indexhub/
RUN pip install .

ARG MODAL_TOKEN_ID
ARG MODAL_TOKEN_SECRET
RUN modal token set --token-id $MODAL_TOKEN_ID --token-secret $MODAL_TOKEN_SECRET --env=functional_analytics
RUN modal env activate functional_analytics

EXPOSE 8000

CMD ["uvicorn", "indexhub.api.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
