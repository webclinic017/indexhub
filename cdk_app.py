import os
from aws_cdk import App, Environment
from cdk.fastapi_stack import FastAPIStack

app = App()

FastAPIStack(
    app,
    "FastAPIStack",
    env=Environment(
        account=os.environ["AWS_ACCOUNT_ID"],
        region=os.environ["AWS_DEFAULT_REGION"],
    ),
)
app.synth()
