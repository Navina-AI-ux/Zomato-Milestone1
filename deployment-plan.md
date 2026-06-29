# Deployment Plan — Zomato AI Recommender

## Architecture Overview

```
Browser
  │
  ├── Frontend (Vercel)
  │     └── ui/index.html  →  static SPA
  │           │
  │           └── API calls  →  Backend (Railway)
  │                                └── FastAPI + Groq + HuggingFace dataset
```

---

## Part 1 — Backend on Railway

### What gets deployed
- FastAPI app (`app/main.py`)
- Loads 51,717 restaurants from HuggingFace on startup
- Exposes `/api/v1/recommend`, `/api/v1/locations`, `/health`

### Step 1 — Add a Procfile
Create `Procfile` in the project root:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Step 2 — Add runtime.txt (optional, pin Python version)
```
python-3.12
```

### Step 3 — Deploy to Railway

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Select `Navina-AI-ux/Zomato-Milestone1`
3. Railway auto-detects Python and installs `requirements.txt`

### Step 4 — Set Environment Variables on Railway
In Railway dashboard → **Variables** tab, add:

| Variable | Value |
|---|---|
| `GROQ_API_KEY` | your Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` |
| `MAX_CANDIDATES` | `30` |
| `TOP_K` | `5` |
| `DATASET_NAME` | `ManikaSaini/zomato-restaurant-recommendation` |
| `PORT` | (Railway sets this automatically — do NOT override) |

### Step 5 — Configure Start Command
In Railway → **Settings** → **Start Command**:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Step 6 — Generate a Domain
Railway dashboard → **Settings** → **Networking** → **Generate Domain**  
Note the URL, e.g. `https://zomato-api-production.up.railway.app`

### Expected startup time
~30–60 seconds (HuggingFace dataset downloads and caches on first boot).  
Railway keeps the container warm — subsequent requests are instant.

---

## Part 2 — Frontend on Vercel

### What gets deployed
- `ui/index.html` — single static HTML file (no build step needed)

### Step 1 — Update the API base URL in index.html

Before deploying, change the `API_BASE` constant in `ui/index.html` from:
```js
const API_BASE = 'http://127.0.0.1:8000';
```
to your Railway backend URL:
```js
const API_BASE = 'https://zomato-api-production.up.railway.app';
```

### Step 2 — Add vercel.json
Create `vercel.json` in the project root to tell Vercel to serve the `ui/` folder:
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/ui/index.html" }],
  "public": "ui"
}
```

### Step 3 — Deploy to Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New Project** → Import `Navina-AI-ux/Zomato-Milestone1`
2. Set **Framework Preset** → `Other`
3. Set **Output Directory** → `ui`
4. Leave Build Command blank (no build needed)
5. Click **Deploy**

Vercel generates a URL like `https://zomato-milestone1.vercel.app`

### Step 4 — Set Environment Variables on Vercel (none required)
The frontend is a static file — all secrets stay on Railway. No env vars needed on Vercel.

---

## Part 3 — CORS Update (Backend)

After getting the Vercel URL, update `app/main.py` to allow requests from it:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://zomato-milestone1.vercel.app",   # your Vercel URL
        "http://127.0.0.1:8000",                   # local dev
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then push to GitHub — Railway and Vercel both auto-redeploy on push.

---

## Deployment Checklist

### Backend (Railway)
- [ ] `Procfile` added to repo root
- [ ] All env vars set in Railway dashboard (`GROQ_API_KEY` etc.)
- [ ] `/health` endpoint returns `200 OK` after deploy
- [ ] `/api/v1/locations` returns location list
- [ ] `/api/v1/recommend` returns results for a test payload

### Frontend (Vercel)
- [ ] `API_BASE` in `ui/index.html` updated to Railway URL
- [ ] `vercel.json` added to repo root
- [ ] Vercel Output Directory set to `ui`
- [ ] Location dropdown loads on page open
- [ ] End-to-end recommendation flow works

---

## Cost Estimate

| Service | Plan | Cost |
|---|---|---|
| Railway | Hobby (500 hrs/month free) | Free tier or ~$5/month |
| Vercel | Free tier (100GB bandwidth/month) | Free |
| Groq API | Free tier (14,400 req/day) | Free |
| HuggingFace dataset | Public dataset | Free |

**Total: $0 to $5/month** depending on Railway usage.

---

## Local → Production Environment Mapping

| Config | Local | Production |
|---|---|---|
| API base URL | `http://127.0.0.1:8000` | Railway HTTPS URL |
| GROQ_API_KEY | `.env` file | Railway env var |
| Dataset | HF cache in `~/.cache/` | HF cache in Railway container |
| Port | `8000` | `$PORT` (Railway assigns) |
| CORS | `allow_origins=["*"]` | Restricted to Vercel URL |
