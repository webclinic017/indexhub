import modal
import os

ENV_PREFIX = os.environ.get("ENV_NAME", "dev")

MOUNT = modal.Mount.from_local_dir(
    "./indexhub", remote_path="/indexhub"
).add_local_file("requirements.txt")

IMAGE = (
    modal.Image.debian_slim(python_version="3.9.10")
    .env(vars={"ENV_NAME": ENV_PREFIX})
    .copy_mount(MOUNT, remote_path="/")
    .run_commands("python3 -m pip install -r requirements.txt")
    .persist(f"{ENV_PREFIX}-indexhub-image")
)

stub = modal.Stub(
    f"{ENV_PREFIX}-indexhub-flows",
    image=IMAGE,
    secrets=[
        modal.Secret.from_name("aws-credentials"),
        modal.Secret.from_name(f"{ENV_PREFIX}-postgres-credentials"),
    ],
)
