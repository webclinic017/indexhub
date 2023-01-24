# indexhub

## Getting Started

Prerequisite:
- Docker (https://docs.docker.com/get-docker/)

```bash
# Setup pre-commit
pre-commit install

# Deploy app in a docker container
docker-compose build --no-cache
docker-compose up
```

Following services will be available once docker container was successfuly built and run
- FastAPI endpoints (API) available at http://localhost:{FASTAPI_PORT}
- FastAPI docs available at http://localhost:{FASTAPI_PORT}/docs
- Postgres Admin panel available at http://localhost:{POSTGRES_ADMIN_PORT}
- React App (FE) available at http://localhost:3000
