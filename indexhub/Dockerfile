FROM python:3.9-slim-bullseye

COPY ./pyproject.toml /app/pyproject.toml

COPY ./README.md /app/README.md

RUN pip install --upgrade pip

ADD indexhub /app/indexhub

RUN pip install ./app

EXPOSE 8000

CMD ["uvicorn", "indexhub.api.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
