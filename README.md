# indexhub

## Getting Started
```bash
# Setup pre-commit
pre-commit install

# Create new conda environment
conda create -n "indexhub" python=3.9
conda activate indexhub
pip install --upgrade pip
# Install indexhub pip package and dependencies
pip install -e ".[dev]"

# Start FastAPI server
uvicorn indexhub.api.server:app --reload
```
