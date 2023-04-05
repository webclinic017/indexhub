FROM python:3.10-slim-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY pyproject.toml pyproject.toml
COPY indexhub indexhub/
RUN pip install .

EXPOSE 8000

CMD ["uvicorn", "indexhub.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
