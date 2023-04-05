import os

ENV = "prod" if (os.getenv("DEBUG", "true").lower()) == "false" else "dev"
AWS_DEFAULT_REGION = os.environ["AWS_DEFAULT_REGION"]
