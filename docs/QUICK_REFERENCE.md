# PhysioAssist AI - Quick Reference

## Cloud Services
- **MongoDB Atlas**: Database (Free M0 tier)
- **Elastic Cloud**: Search engine (14-day trial)
- **Render**: Hosting platform (Free tier)

## Deployed Services
- **Backend**: https://physioassist-ai.onrender.com
- **Frontend**: https://physioassist-ai-frontend.onrender.com

## Local Development (Docker)
```bash
podman-compose up -d                    # Start all services
```
- Frontend: http://localhost:8502
- Backend: http://localhost:8002/docs

## Environment Variables (Render)

### Backend Service
- OPENAI_API_KEY
- MONGODB_CONNECTION_STRING (Atlas)
- MONGODB_DATABASE_NAME=v33
- ELASTIC_SEARCH_ENDPOINT (Cloud)
- ELASTIC_SEARCH_KEY (Cloud)

### Frontend Service
- API_BASE_URL=https://physioassist-ai.onrender.com

## Deploy Updates
```bash
git push origin deploy                  # Auto-deploys to Render (~5 min)
```

## Initialize Search Index
```bash
curl -X POST https://physioassist-ai.onrender.com/data/ingest \
  -H "Content-Type: application/json" \
  -d '{"index_name": "physiotherapy_injuries", "recreate_index": true}'
```
