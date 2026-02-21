# Deploy React Frontend on Render

## Option A: Manual Web Service

- Runtime: Node
- Root Directory: frontend-react
- Build Command: npm ci && npm run build
- Start Command: npm start
- Env var: VITE_API_BASE_URL=https://physioassist-ai.onrender.com

## Option B: Blueprint

Use [frontend-react/render.yaml](render.yaml) as a Render Blueprint.

## Backend CORS

Set backend env var on Render:
- CORS_ORIGINS=https://your-frontend-url.onrender.com,http://localhost:5173

(Regex for onrender domains is already enabled in backend defaults.)
