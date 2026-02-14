# PhysioAssist AI - Deployment Guide

## Cloud Services Used

### 🗄️ MongoDB Atlas
**Database Service** - Cloud-hosted MongoDB for persistent data storage

- **Provider**: MongoDB Atlas (https://www.mongodb.com/atlas)
- **Tier**: Free (M0 Sandbox)
- **Region**: Choose closest to your deployment
- **Purpose**: Stores injury data, chat sessions, and application state
- **Connection**: Via connection string environment variable
- **Setup**:
  1. Create account at https://www.mongodb.com/cloud/atlas/register
  2. Create a free M0 cluster
  3. Configure network access (allow from anywhere: 0.0.0.0/0)
  4. Create database user
  5. Get connection string and add to environment variables

### 🔍 Elastic Cloud
**Search Service** - Managed Elasticsearch for semantic search

- **Provider**: Elastic Cloud (https://cloud.elastic.co)
- **Tier**: Free trial (14 days, then paid)
- **Region**: Choose closest to your deployment
- **Version**: Elasticsearch 8.x
- **Purpose**: Powers hybrid search (semantic + keyword) for injury knowledge base
- **Authentication**: API key authentication
- **Setup**:
  1. Create account at https://cloud.elastic.co/registration
  2. Create a deployment
  3. Copy the Cloud ID/Endpoint URL (format: https://xxx.region.cloud.es.io:443)
  4. Generate API key from deployment management console
  5. Add endpoint and API key to environment variables

### ☁️ Render
**Hosting Platform** - Cloud platform for deploying applications

- **Provider**: Render (https://render.com)
- **Tier**: Free tier (with limitations)
- **Region**: US-Central (or your preference)
- **Purpose**: Hosts both frontend and backend services
- **Deployments**: 
  - **Backend Service** (FastAPI): https://physioassist-ai.onrender.com
  - **Frontend Service** (Streamlit): https://physioassist-ai-frontend.onrender.com
- **Setup**:
  1. Create account at https://render.com
  2. Connect GitHub repository
  3. Create two Web Services (backend + frontend)
  4. Configure environment variables for each service
  5. Auto-deploys on git push to `deploy` branch

### 📊 Architecture Overview
```
User Browser
    ↓
Streamlit Frontend (Render)
    ↓
FastAPI Backend (Render)
    ↓
    ├─→ MongoDB Atlas (Database)
    └─→ Elastic Cloud (Search)
```

---

## Quick Start Guide

### 🐳 Option 1: Docker Deployment (Recommended)

**All services in containers - easiest way to deploy!**

**1. Start all services:**
```bash
cd PhysioAssist-AI
podman-compose up -d
```

**2. Access your application:**
- **Frontend (Streamlit):** http://localhost:8502
- **Backend API:** http://localhost:8002
- **API Documentation:** http://localhost:8002/docs

**3. Stop services:**
```bash
podman-compose down
```

**Ports used by Docker:**
| Service | External Port | Internal Port |
|---------|--------------|---------------|
| Streamlit Frontend | 8502 | 8501 |
| FastAPI Backend | 8002 | 8002 |
| MongoDB | 27018 | 27017 |
| Elasticsearch | 9201 | 9200 |

---

### 💻 Option 2: Local Development (Native)

**Run services locally for development - requires local setup.**

**Prerequisites:**
- Python 3.11+
- Your own MongoDB instance on port 27017
- Your own Elasticsearch instance on port 9200

**1. Install dependencies:**
```bash
cd PhysioAssist-AI
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Configure environment:**
Create `.env` file:
```bash
OPENAI_API_KEY=sk-your-key-here
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9201
ELASTICSEARCH_SCHEME=http
MONGODB_CONNECTION_STRING=mongodb://admin:physioassist_pass@localhost:27018/
MONGODB_DATABASE_NAME=physioassist
```

**3. Start backend:**
```bash
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8002
```

**4. Start frontend (in another terminal):**
```bash
source .venv/bin/activate
streamlit run streamlit_app.py
```

**5. Access your application:**
- **Frontend (Streamlit):** http://localhost:8501
- **Backend API:** http://localhost:8002
- **API Documentation:** http://localhost:8002/docs

**Ports used by Local:**
| Service | Port |
|---------|------|
| Streamlit Frontend | 8501 |
| FastAPI Backend | 8001 |
| MongoDB (your local) | 27017 |
| Elasticsearch (your local) | 9200 |

---

### 🔄 Hybrid: Local + Docker Databases

**Best for development - code locally, use Docker for databases.**

**1. Start only databases in Docker:**
```bash
podman-compose up -d mongodb elasticsearch
```

**2. Create `.env` file to use Docker databases:**
```bash
OPENAI_API_KEY=sk-your-key-here
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9201
ELASTICSEARCH_SCHEME=http
MONGODB_CONNECTION_STRING=mongodb://admin:physioassist_pass@localhost:27018/
MONGODB_DATABASE_NAME=physioassist
```

**3. Start local backend:**
```bash
source .venv/bin/activate
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8001
```

**4. Start local frontend:**
```bash
streamlit run streamlit_app.py
```

**Ports:**
- Frontend: **8501** (local)
- Backend: **8001** (local)
- MongoDB: **27018** (Docker)
- Elasticsearch: **9201** (Docker)

---

## Common Commands

### Docker (Podman/Docker)

```bash
# Start all services
podman-compose up -d

# View logs
podman logs physioassist-backend
podman logs physioassist-frontend

# Check status
podman-compose ps

# Restart a service
podman-compose restart backend

# Stop all services
podman-compose down

# Stop and remove all data (fresh start)
podman-compose down -v

# Rebuild after code changes
podman-compose up -d --build
```

### Local Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Start backend
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8001

# Start frontend
streamlit run streamlit_app.py

# Run tests
pytest

# Check code formatting
black src/
```

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Cloud Deployment Options](#cloud-deployment-options)
3. [Production Considerations](#production-considerations)
4. [Environment Variables](#environment-variables)
5. [Monitoring & Scaling](#monitoring--scaling)

---

## Prerequisites
- **Docker Desktop** OR **Podman** installed
- **Docker Compose** OR **podman-compose** installed
- OpenAI API key
- At least 4GB RAM available

> **Note:** Podman is a drop-in replacement for Docker. All commands work with both!

### Quick Start

1. **Clone and setup environment:**
```bash
git clone <your-repo>
cd PhysioAssist-AI
cp .env.example .env
```

2. **Configure `.env` file:**
```bash
# Required: Add your OpenAI API key
OPENAI_API_KEY=sk-your-key-here

# Other settings are pre-configured
```

3. **Start all services:**

**Using Docker:**
```bash
docker-compose up -d
```

**Using Podman:**
```bash
podman-compose up -d
# OR use docker alias:
alias docker=podman
alias docker-compose=podman-compose
docker-compose up -d
```

4. **Wait for services to be ready (30-60 seconds):**
```bash
# Docker
docker-compose logs -f backend

# Podman
podman-compose logs -f backend
```

5. **Access the application:**
- **Frontend (Streamlit):** http://localhost:8502
- **Backend API (Docker):** http://localhost:8002
- **API Docs:** http://localhost:8002/docs
- **MongoDB:** localhost:27018
- **Elasticsearch:** http://localhost:9201

6. **Import sample data:**
```bash
# Docker
docker-compose exec backend python scripts/import_injuries_to_mongo.py

# Podman
podman-compose exec backend python scripts/import_injuries_to_mongo.py
```

### Container Commands

**Docker:**
```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# Rebuild after code changes
docker-compose up -d --build
```

**Podman:**
```bash
# View logs
podman-compose logs -f backend
podman-compose logs -f frontend

# Restart services
podman-compose restart

# Stop services
podman-compose down

# Stop and remove volumes (fresh start)
podman-compose down -v

# Rebuild after code changes
podman-compose up -d --build
```

### Podman-Specific Notes

If you don't have `podman-compose`, install it:
```bash
# macOS
brew install podman-compose

# Linux
pip install podman-compose
```

**Create aliases for convenience:**
```bash
# Add to ~/.zshrc or ~/.bashrc
alias docker=podman
alias docker-compose=podman-compose
```

---

## Cloud Deployment Options

### Option 1: Railway (Recommended for Quick Deploy)

**Pros:** Easy setup, free tier, automatic deploys from GitHub

1. **Prepare your repository:**
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

2. **Deploy to Railway:**
- Go to [railway.app](https://railway.app)
- Click "New Project" → "Deploy from GitHub repo"
- Select your repository
- Railway will detect `docker-compose.yml` and deploy automatically

3. **Add environment variables in Railway dashboard:**
```
OPENAI_API_KEY=sk-your-key-here
EMBEDDING_PROVIDER=openai
SEARCH_SERVICE=elasticsearch
```

4. **Services will be available at:**
- Frontend: `https://your-app.railway.app`
- Backend: `https://your-api.railway.app`

**Estimated Cost:** Free tier available, ~$5-20/month for production

---

### Option 2: AWS (Production-Ready)

**Pros:** Full control, scalable, enterprise-grade

**Architecture:**
```
ECS (Backend) + CloudFront (Frontend) + RDS/MongoDB Atlas + OpenSearch/Elasticsearch Service
```

**Steps:**

1. **MongoDB Atlas (Managed MongoDB):**
```bash
# Sign up at mongodb.com/atlas
# Create a cluster (M0 free tier available)
# Get connection string: mongodb+srv://...
```

2. **Elasticsearch Service:**
```bash
# Use AWS OpenSearch Service or Elastic Cloud
# Note the endpoint URL
```

3. **Deploy Backend (ECS with Fargate):**
```bash
# Build and push Docker image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker build -t physioassist-backend .
docker tag physioassist-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/physioassist-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/physioassist-backend:latest

# Create ECS task definition and service (use AWS Console or Terraform)
```

4. **Deploy Frontend (S3 + CloudFront or ECS):**

**Option A - Static hosting (requires converting Streamlit to React):**
```bash
# Not recommended for Streamlit
```

**Option B - Container on ECS:**
```bash
docker build -f Dockerfile.streamlit -t physioassist-frontend .
# Push to ECR and deploy like backend
```

**Estimated Cost:** ~$50-200/month depending on usage

---

### Option 3: Google Cloud Platform

**Pros:** Good AI/ML integration, competitive pricing

**Architecture:**
```
Cloud Run (Backend) + Cloud Run (Frontend) + MongoDB Atlas + Elasticsearch Service
```

**Steps:**

1. **Enable required APIs:**
```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

2. **Deploy Backend:**
```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/physioassist-backend

# Deploy to Cloud Run
gcloud run deploy physioassist-backend \
  --image gcr.io/PROJECT_ID/physioassist-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=sk-xxx,MONGODB_CONNECTION_STRING=mongodb+srv://...
```

3. **Deploy Frontend:**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/physioassist-frontend -f Dockerfile.streamlit

gcloud run deploy physioassist-frontend \
  --image gcr.io/PROJECT_ID/physioassist-frontend \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars API_BASE_URL=https://backend-xxx.run.app
```

**Estimated Cost:** ~$20-100/month

---

### Option 4: Render.com (Simple, Like Heroku)

**Pros:** Free tier, easy to use, automatic HTTPS

1. **Sign up at render.com**

2. **Create a new Web Service:**
- Connect your GitHub repo
- Select "Docker" as environment
- Use `Dockerfile` for backend

3. **Add environment variables**

4. **Deploy frontend:**
- Create another Web Service
- Use `Dockerfile.streamlit`

**Estimated Cost:** Free tier available, ~$7-15/month per service

---

## Production Considerations

### 1. Security

**API Keys:**
```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use secrets management:
# - AWS Secrets Manager
# - Google Secret Manager
# - HashiCorp Vault
```

**Add authentication to APIs:**
```python
# Add to src/app/api/dependencies.py
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != settings.API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials
```

### 2. Database

**MongoDB Production:**
- Use **MongoDB Atlas** (managed, free tier available)
- Enable authentication
- Set up backups
- Configure indexes:

```python
# Add indexes for better performance
collection.create_index([("title", pymongo.TEXT)])
collection.create_index([("tags", pymongo.ASCENDING)])
```

**Elasticsearch Production:**
- Use **Elastic Cloud** or **AWS OpenSearch**
- Configure snapshots for backups
- Set up index lifecycle management
- Monitor cluster health

### 3. Monitoring

**Add health checks:**
```python
# Already in place at /health endpoint
# Monitor: response time, error rate, uptime
```

**Logging:**
```python
# Configure structured logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Recommended tools:**
- **Sentry** for error tracking
- **Datadog** or **New Relic** for APM
- **Prometheus + Grafana** for metrics

### 4. Scaling

**Horizontal Scaling:**
```yaml
# In docker-compose.yml
backend:
  deploy:
    replicas: 3
  # Add load balancer (nginx, traefik)
```

**Caching:**
```python
# Add Redis for caching search results
from redis import Redis
cache = Redis(host='redis', port=6379)

@router.get("/search/")
async def search(query: str):
    cached = cache.get(f"search:{query}")
    if cached:
        return json.loads(cached)
    # ... perform search ...
    cache.setex(f"search:{query}", 3600, json.dumps(results))
```

**CDN:**
- Use CloudFront (AWS) or Cloud CDN (GCP) for frontend
- Cache static assets

### 5. Cost Optimization

**Tips:**
1. Use free tiers where possible:
   - MongoDB Atlas M0 (512MB free)
   - Railway (starter projects)
   - Render (static sites free)

2. Optimize OpenAI costs:
   - Cache embeddings
   - Use smaller models where appropriate
   - Implement rate limiting

3. Right-size resources:
   - Start small, scale up based on metrics
   - Use auto-scaling
   - Set up alerts for cost spikes

---

## Cloud Deployment (Render)

### Prerequisites
- GitHub account with repository
- Render account (https://render.com)
- MongoDB Atlas account and cluster
- Elastic Cloud account and deployment

### Backend Service Deployment

**1. Create Web Service on Render:**
- **Name**: `physioassist-ai` (or your choice)
- **Repository**: Your GitHub repo (e.g., AhmedAshraf82/PhysioAssist-AI)
- **Branch**: `deploy`
- **Root Directory**: Leave blank
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn src.app.main:app --host 0.0.0.0 --port $PORT`
- **Instance Type**: Free

**2. Environment Variables for Backend:**
```bash
# OpenAI
OPENAI_API_KEY=sk-proj-...

# MongoDB Atlas
MONGODB_CONNECTION_STRING=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE_NAME=v33
MONGODB_COLLECTION_NAME=injuries

# Elastic Cloud
ELASTIC_SEARCH_ENDPOINT=https://xxxxx.us-central1.gcp.cloud.es.io:443
ELASTIC_SEARCH_KEY=your_api_key_here

# Search Configuration
SEARCH_SERVICE=elasticsearch
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

**3. Deploy:**
- Render will automatically build and deploy
- Wait ~5-10 minutes for first deployment
- Note your backend URL: `https://physioassist-ai.onrender.com`

### Frontend Service Deployment

**1. Create Another Web Service:**
- **Name**: `physioassist-ai-frontend`
- **Repository**: Same GitHub repo
- **Branch**: `deploy`
- **Root Directory**: Leave blank
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
- **Instance Type**: Free

**2. Environment Variable for Frontend:**
```bash
API_BASE_URL=https://physioassist-ai.onrender.com
```

**3. Deploy:**
- Frontend will deploy automatically
- Access at: `https://physioassist-ai-frontend.onrender.com`

### Post-Deployment Setup

**1. Initialize Elasticsearch Index:**
```bash
curl -X POST https://physioassist-ai.onrender.com/data/ingest \
  -H "Content-Type: application/json" \
  -d '{"index_name": "physiotherapy_injuries", "recreate_index": true}'
```

**2. Verify Services:**
- Backend health: https://physioassist-ai.onrender.com/health
- Backend docs: https://physioassist-ai.onrender.com/docs
- Frontend app: https://physioassist-ai-frontend.onrender.com

### Important Notes

**Free Tier Limitations:**
- Services spin down after 15 minutes of inactivity
- First request after spin down takes 30-60 seconds (cold start)
- 750 hours/month free (enough for 1 service 24/7)

**Auto-Deploy:**
- Push to `deploy` branch triggers automatic redeployment
- Monitor build logs in Render dashboard
- Deployments take ~5-10 minutes

**Troubleshooting:**
- Check Render logs for errors
- Verify all environment variables are set
- Ensure MongoDB Atlas network access allows Render IPs (0.0.0.0/0)
- Confirm Elastic Cloud is accessible

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `MONGODB_CONNECTION_STRING` | MongoDB connection | `mongodb+srv://...` or `mongodb://...` |
| `MONGODB_DATABASE_NAME` | Database name | `v33` |
| `MONGODB_COLLECTION_NAME` | Collection name | `injuries` |
| `ELASTIC_SEARCH_ENDPOINT` | Elastic Cloud endpoint | `https://xxx.cloud.es.io:443` |
| `ELASTIC_SEARCH_KEY` | Elastic Cloud API key | `base64_encoded_key` |
| `API_BASE_URL` | Backend URL (frontend only) | `https://your-backend.onrender.com` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `EMBEDDING_PROVIDER` | openai or aws_bedrock | `openai` |
| `EMBEDDING_MODEL` | Embedding model name | `text-embedding-3-small` |
| `EMBEDDING_DIMENSIONS` | Embedding dimensions | `1536` |
| `SEARCH_SERVICE` | elasticsearch or opensearch | `elasticsearch` |
| `LOG_LEVEL` | Logging level | `INFO` |

---

## Monitoring & Scaling

### Health Checks

```bash
# Backend health
curl http://localhost:8001/health

# Elasticsearch health
curl http://localhost:9201/_cluster/health

# MongoDB health
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### Performance Monitoring

**Key metrics to track:**
1. API response time (target: <500ms)
2. Error rate (target: <1%)
3. Search latency (target: <200ms)
4. Database query time
5. Memory usage
6. CPU usage

**Set up alerts:**
- Response time > 1s
- Error rate > 5%
- Disk usage > 80%
- Memory usage > 85%

---

## Troubleshooting

**Common Issues:**

1. **"Connection refused" errors:**
```bash
# Check if all services are running
docker-compose ps

# Check logs
docker-compose logs backend
```

2. **Elasticsearch not ready:**
```bash
# Wait for health check
docker-compose logs elasticsearch | grep "Cluster health status"
```

3. **MongoDB connection issues:**
```bash
# Test connection
docker-compose exec mongodb mongosh -u admin -p physioassist_pass
```

4. **Out of memory:**
```bash
# Increase Docker memory limit in Docker Desktop
# Or reduce Elasticsearch heap size in docker-compose.yml
```

---

## Quick Deploy Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] Add `OPENAI_API_KEY` to `.env`
- [ ] Run `docker-compose up -d`
- [ ] Wait for services to start (check logs)
- [ ] Import sample data
- [ ] Test frontend at http://localhost:8501
- [ ] Test API at http://localhost:8001/docs
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Set up CI/CD (optional)

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Review [API documentation](http://localhost:8001/docs)
3. Check MongoDB data: `docker-compose exec mongodb mongosh`
4. Test Elasticsearch: `curl http://localhost:9201/_cat/indices`
