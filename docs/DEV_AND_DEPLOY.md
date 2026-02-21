# PhysioAssist - Development & Deployment

## 1) Local development setup

### Backend (FastAPI)
1. Copy env file:
   - `cp .env.example .env`
2. Activate Python env and install deps:
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
3. Start backend:
   - `uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8002`
4. Verify backend:
   - http://localhost:8002/health
   - http://localhost:8002/docs

### Databases (local with Docker/Podman)
1. Start infra:
   - `podman compose up -d mongodb elasticsearch`
2. Confirm ports:
   - MongoDB: `27018`
   - Elasticsearch: `9201`

### Frontend (React)
1. Go to frontend:
   - `cd frontend-react`
2. Create frontend env:
   - `cp .env.example .env`
3. Install and run:
   - `npm install`
   - `npm run dev`
4. Open:
   - http://localhost:5173

Demo login:
- Username: `ziad_baher10`
- Password: `password`

---

## 2) Deploy on Render (recommended)

You can deploy via Blueprint using root `render.yaml`.

### Option A: Blueprint deploy
1. Push code to `deploy` branch.
2. In Render, create from Blueprint and select repo.
3. Render creates two services:
   - Backend: `physioassist-ai`
   - Frontend: `physioassist-ai-frontend-react`
4. Set secret vars in backend service:
   - `OPENAI_API_KEY`
   - `MONGODB_CONNECTION_STRING`
   - `ELASTIC_SEARCH_ENDPOINT`
   - `ELASTIC_SEARCH_KEY`
5. Update backend CORS_ORIGINS with your frontend URL after first deploy:
   - `https://your-frontend.onrender.com,http://localhost:5173`
6. Redeploy backend.

### Option B: Manual deploy
- Backend:
  - Runtime: Python
  - Build: `pip install -r requirements.txt`
  - Start: `uvicorn src.app.main:app --host 0.0.0.0 --port $PORT`
- Frontend:
  - Runtime: Node
  - Root dir: `frontend-react`
  - Build: `npm ci && npm run build`
  - Start: `npm start`
  - Env: `VITE_API_BASE_URL=https://<backend>.onrender.com`

---

## 3) First run after deployment

1. Open frontend URL and login.
2. Click **Data Ingestion** once to index data.
3. Use search bar and chat page.

---

## 4) Troubleshooting

- 403/CORS errors: verify `CORS_ORIGINS` and redeploy backend.
- Slow first response: free tier cold start (30–60s).
- Search fails: verify Elastic Cloud endpoint/key.
- Chat/session fails: verify MongoDB Atlas connection string and IP allow list.
