import modal

MOUNT = modal.Mount.from_local_dir(
    "./indexhub", remote_path="/indexhub"
).add_local_file("requirements.txt")

IMAGE = (
    modal.Image.debian_slim(python_version="3.9.10")
    .copy(MOUNT, remote_path="/")
    .run_commands("python3 -m pip install -r requirements.txt")
    .persist("indexhub-image")
)
