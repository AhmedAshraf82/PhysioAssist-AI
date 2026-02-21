# PhysioAssist-AI

An AI-powered physiotherapy assistant application built with FastAPI.

## Current stack

- Backend: FastAPI ([src/app/main.py](src/app/main.py))
- Frontend: React + Vite ([frontend-react](frontend-react))
- Databases/Search: MongoDB + Elasticsearch

## Quick links

- Development + deployment guide: [docs/DEV_AND_DEPLOY.md](docs/DEV_AND_DEPLOY.md)
- Render blueprint (backend + frontend): [render.yaml](render.yaml)
- React frontend guide: [frontend-react/README.md](frontend-react/README.md)

## Project Structure

```
PhysioAssist-AI/
├── src/
│   └── app/
│       ├── api/              # API layer
│       │   ├── routes/       # API endpoints/routes
│       │   ├── dependencies.py
│       │   └── middlewares.py
│       ├── core/             # Core configuration
│       │   └── config.py
│       ├── schemas/          # Pydantic models (request/response)
│       ├── services/         # Business logic
│       │   └── model_service.py
│       ├── models/           # ML models
│       └── utils/            # Utility functions
├── tests/                    # Tests
├── data/                     # Data files
│   ├── raw/
│   └── processed/
├── notebooks/                # Jupyter notebooks
├── config/                   # Additional configs
└── requirements.txt
```

## Setup

### Prerequisites
Install uv (fast Python package installer):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# or on macOS
brew install uv
```

### Installation

1. Create a virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
uv pip install -r requirements.txt
```

3. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

> **Note:** Using `uv` for 10-100x faster package installation. You can also use standard `pip` if preferred.

## Running the Application

Start the FastAPI server:
```bash
# Make sure your venv is activated
source .venv/bin/activate

# Development mode with auto-reload
python -m src.app.main

# Or using uvicorn directly
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8002
```

The API will be available at:
- API: http://localhost:8002
- Interactive docs (Swagger): http://localhost:8002/docs
- Alternative docs (ReDoc): http://localhost:8002/redoc

## API Endpoints

- `GET /api/v1/` - Root endpoint
- `GET /api/v1/health` - Health check
- `POST /api/v1/predictions/` - Create prediction

## Development

### Project Structure Explanation

- **api/routes/**: Contains all API endpoint definitions
- **schemas/**: Pydantic models for request validation and response serialization
- **services/**: Business logic layer, separated from API routes
- **core/**: Core configuration and settings
- **models/**: ML model definitions and related code

### Adding New Routes

1. Create a new file in `src/app/api/routes/`
2. Define your router and endpoints
3. Include the router in `src/app/main.py`

Example:
```python
# src/app/api/routes/new_feature.py
from fastapi import APIRouter

router = APIRouter(prefix="/feature", tags=["feature"])

@router.get("/")
async def get_feature():
    return {"message": "New feature"}
```

## Testing

Run tests:
```bash
pytest
```

## License

TODO: Add license information
