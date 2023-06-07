import modal
import os

MOUNT = modal.Mount.from_local_dir(
    "./indexhub", remote_path="/indexhub"
).add_local_file("requirements.txt")

IMAGE = (
    modal.Image.debian_slim(python_version="3.9.10")
    .copy_mount(MOUNT, remote_path="/")
    .run_commands("python3 -m pip install -r requirements.txt")
    .persist("indexhub-image")
)

env_prefix = os.environ.get("ENV_NAME", "dev")
stub = modal.Stub(
    f"{env_prefix}-indexhub-flows",
    image=IMAGE,
    secrets=[
        modal.Secret.from_name("aws-credentials"),
        modal.Secret.from_name("postgres-credentials"),
        modal.Secret.from_name("env-name"),
    ],
)
