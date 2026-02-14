# Port Configuration

## Summary of Port Fixes

This document outlines the corrected port configuration for PhysioAssist-AI to ensure consistency between local development and Docker deployment.

## Service Ports

### Services (Both Local & Docker)

| Service | Docker Port Mapping | Local Port | Container Internal Port |
|---------|-------------------|------------|------------------------|
| **MongoDB** | 27018:27017 | 27018 | 27017 |
| **Elasticsearch** | 9201:9200 | 9201 | 9200 |
| **Backend (FastAPI)** | 8002:8002 | 8002 | 8002 |
| **Frontend (Streamlit)** | 8502:8501 | 8501 | 8501 |

## Fixed Files

### 1. Backend Port (8001 → 8002)
- **File**: `src/app/main.py`
- **Change**: Updated `uvicorn.run(app, host="0.0.0.0", port=8002)`
- **Reason**: Match Docker configuration

### 2. Streamlit API URL (8001 → 8002)
- **File**: `streamlit_app.py`
- **Change**: Updated default API_BASE_URL to `http://localhost:8002`
- **Reason**: Point to correct backend port

### 3. Elasticsearch Port & Scheme
- **File**: `src/app/core/config.py`
- **Changes**: 
  - Port: 9200 → 9201 (matches Docker port mapping)
  - Scheme: https → http (matches Docker setup with security disabled)
- **Reason**: Align with Docker Compose configuration

### 4. Documentation
- **File**: `README.md`
- **Change**: Updated all port references to 8002
- **Reason**: Keep docs in sync with actual configuration

## Environment Variables (.env)

Ensure your `.env` file has these settings for local development:

```env
# MongoDB
MONGODB_CONNECTION_STRING=mongodb://admin:physioassist_pass@localhost:27018/
MONGODB_DATABASE_NAME=v33

# Elasticsearch
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9201
ELASTICSEARCH_SCHEME=http
```

## Running Locally

### 1. Start Docker Services (MongoDB & Elasticsearch)
```bash
docker-compose up -d mongodb elasticsearch
```

### 2. Start Backend
```bash
python -m src.app.main
# or
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8002
```
Backend will be available at: http://localhost:8002

### 3. Start Frontend (Optional)
```bash
streamlit run streamlit_app.py
```
Frontend will be available at: http://localhost:8501

## Running with Docker Compose

```bash
docker-compose up
```

All services will start automatically:
- MongoDB: localhost:27018
- Elasticsearch: localhost:9201
- Backend API: localhost:8002
- Streamlit UI: localhost:8502

## Key Points

1. **Consistency**: All configurations now use port 8002 for the backend
2. **Docker Mapping**: Docker exposes services on different ports to avoid conflicts
3. **No Conflicts**: All ports are properly mapped and don't conflict with common services
4. **.env**: Your `.env` already had the correct Elasticsearch port (9201)

## Troubleshooting

If you still face issues:

1. **Check if ports are in use**:
```bash
lsof -i :8002  # Backend
lsof -i :9201  # Elasticsearch
lsof -i :27018 # MongoDB
lsof -i :8501  # Streamlit
```

2. **Stop any conflicting services**:
```bash
kill -9 <PID>
```

3. **Verify Docker services are running**:
```bash
docker-compose ps
```

4. **Check logs**:
```bash
docker-compose logs -f backend
docker-compose logs -f elasticsearch
```
