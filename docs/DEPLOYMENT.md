# Deployment Guide
## Sub-10ms Context Retrieval Voice Agents

This guide provides step-by-step instructions for deploying the Tandem Voice Agent stack to production:
- **Web Dashboard:** Vercel / Cloudflare Pages (Next.js)
- **Control Plane:** Render / Fly.io / Railway (FastAPI)
- **Agent Worker:** Persistent VM / Fly.io Machines / Render Background Worker (Python LiveKit Agent)
- **SFU Transport:** LiveKit Cloud

---

## 1. Prerequisites & Environment Variables

Ensure the following variables are configured across deployment environments:

| Variable | Description | Example / Default |
|---|---|---|
| `LIVEKIT_URL` | LiveKit Cloud WebSocket URL | `wss://parity-9hhf288x.livekit.cloud` |
| `LIVEKIT_API_KEY` | LiveKit API Key | `APIhbPmuykk...` |
| `LIVEKIT_API_SECRET` | LiveKit API Secret | `kQAl7kyhJ6...` |
| `MOSS_PROJECT_ID` | Moss Project UUID | `bbbe10ba-70bd-4ba2-ba91-df87740df27d` |
| `MOSS_PROJECT_KEY` | Moss Project API Key | `moss_742779800...` |
| `GROQ_API_KEY` | Groq LLM API Key | `gsk_APTgdyS...` |
| `DATABASE_URL` | Neon PostgreSQL Database URL | `postgresql://...` |
| `NEXT_PUBLIC_CONTROL_PLANE_URL` | Public URL of FastAPI API | `https://api.yourdomain.com` |
| `NEXT_PUBLIC_LIVEKIT_URL` | Public LiveKit WS URL | `wss://parity-9hhf288x.livekit.cloud` |

---

## 2. Deploying Next.js Dashboard to Vercel

```bash
cd web
npm install -g vercel
vercel
```

Configure the following environment variables in the Vercel Dashboard:
- `NEXT_PUBLIC_CONTROL_PLANE_URL`: Your deployed FastAPI backend URL.
- `NEXT_PUBLIC_LIVEKIT_URL`: Your LiveKit Cloud WebSocket URL.

---

## 3. Deploying FastAPI Control Plane to Render or Fly.io

### Render Setup (Web Service)
1. Create a new **Web Service** pointing to this repository.
2. Root directory: `.`
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python -m uvicorn server.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `MOSS_PROJECT_ID`, `MOSS_PROJECT_KEY`, `GROQ_API_KEY`.

### Fly.io Setup
```bash
fly launch --name tandem-control-plane
fly secrets set LIVEKIT_URL=... LIVEKIT_API_KEY=... LIVEKIT_API_SECRET=... MOSS_PROJECT_ID=... MOSS_PROJECT_KEY=... GROQ_API_KEY=...
fly deploy
```

---

## 4. Deploying Python Agent Worker to Fly.io or Persistent VM

The Agent Worker maintains a persistent connection to LiveKit Cloud via WebSockets to dispatch incoming room calls.

Create `Dockerfile.agent`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ libasound2-dev libportaudio2 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "agent.worker", "start"]
```

Deploy to Fly.io as a worker process:
```bash
fly launch --dockerfile Dockerfile.agent --name tandem-agent-worker
fly scale count 2
```
