# 📊 Sales Insight Automator

> **Rabbitt AI · Sprint Deliverable**  
> Upload raw sales data → AI-generated executive brief → Delivered to inbox.

[![CI Status](https://github.com/YOUR_USERNAME/sales-insight-automator/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/sales-insight-automator/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🔗 Live Access

| Service | URL |
|---------|-----|
| **Frontend** | `https://sales-insight-automator.vercel.app` |
| **Backend API** | `https://sales-insight-api.onrender.com` |
| **Swagger Docs** | `https://sales-insight-api.onrender.com/docs` |
| **ReDoc** | `https://sales-insight-api.onrender.com/redoc` |

---

## 🏗️ Architecture Overview

```
┌─────────────────┐     ┌──────────────────────────────────────────┐
│   React SPA     │────▶│           FastAPI Backend                 │
│   (Vercel)      │     │           (Render / Docker)               │
│                 │     │  ┌────────────┐  ┌──────────────────────┐ │
│  • File Upload  │     │  │ FileParser │  │  AI Engine (Gemini)  │ │
│  • Email Input  │     │  │ (pandas)   │  │  - Prompt builder    │ │
│  • Status Feed  │     │  └────────────┘  │  - Summary gen       │ │
└─────────────────┘     │        │         └──────────────────────┘ │
                        │        ▼                    │              │
                        │  ┌────────────┐             ▼              │
                        │  │  Validator │  ┌──────────────────────┐ │
                        │  │  • Email   │  │  Email Service       │ │
                        │  │  • FileExt │  │  (SMTP / Gmail)      │ │
                        │  │  • Size    │  └──────────────────────┘ │
                        │  └────────────┘                           │
                        └──────────────────────────────────────────┘
```

### End-to-End Flow

1. User uploads `.csv` or `.xlsx` + enters recipient email on the SPA
2. Frontend POSTs `multipart/form-data` to `/api/v1/upload`
3. Backend validates file type, size, and email format
4. `FileParser` loads file into a pandas DataFrame and computes key stats
5. `AIEngine` builds a structured prompt and calls the Gemini API
6. A polished HTML email is sent via SMTP (background task)
7. API returns a `200` with a summary preview — frontend shows success state

---

## 🚀 Local Development (Docker Compose)

### Prerequisites

- Docker 24+ and Docker Compose v2
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- A Gmail account with an [App Password](https://support.google.com/accounts/answer/185833) (for email delivery)

### Step 1 – Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/sales-insight-automator.git
cd sales-insight-automator
```

### Step 2 – Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
GEMINI_API_KEY=AIza...           # Your Gemini API key
SMTP_USER=you@gmail.com          # Gmail sender address
SMTP_PASSWORD=xxxx xxxx xxxx     # Gmail App Password (16 chars)
```

### Step 3 – Spin up the stack

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |

### Step 4 – Test with sample data

Download the reference CSV from the Swagger UI at `/api/v1/sample-data`, then upload it via the frontend or directly via Swagger.

---

## 🔧 Running Without Docker

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env  # then fill in values
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
REACT_APP_API_URL=http://localhost:8000 npm start
```

---

## 🔒 Security Implementation

This section explains how the API endpoints are secured against common vulnerabilities:

### 1. Rate Limiting (Resource Abuse)
**Middleware:** `RateLimitMiddleware` in `backend/app/middleware/rate_limit.py`  
**Strategy:** Sliding window per IP address — **10 requests per 60 seconds**.  
Headers returned: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`.  
Violations return `429 Too Many Requests` with a retry-after time.

### 2. Input Validation (Injection / Abuse)
**Service:** `backend/app/services/validator.py`

| Check | Detail |
|-------|--------|
| **File extension whitelist** | Only `.csv`, `.xlsx`, `.xls` accepted |
| **File size cap** | Max 10 MB enforced before any processing |
| **Magic byte check** | Excel files verified against `PK` header (ZIP format) |
| **Email regex validation** | RFC-compliant regex prevents malformed/injected values |
| **Empty file rejection** | Zero-byte uploads are rejected immediately |

### 3. Security Headers (XSS / Clickjacking / MIME Sniffing)
**Middleware:** `SecurityHeadersMiddleware` in `backend/app/middleware/security.py`  
Applied to every response:

```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Content-Security-Policy: default-src 'self'; ...
```
The `Server` header is also stripped to prevent fingerprinting.

### 4. CORS Configuration
Configured in `main.py` via FastAPI's `CORSMiddleware`.  
- Development: `*` (open for local testing)
- Production: Restrict `allow_origins` to your exact frontend domain

### 5. Non-Root Docker Container
The backend container runs as `appuser` (UID 1001), not `root`, following the principle of least privilege.

### 6. Secrets Management
- All credentials are loaded from environment variables (`.env`)
- `.env` is in `.gitignore` — never committed
- A `.env.example` with no real values is committed for reference

---

## ☁️ Deployment Guide

### Backend → Render

1. Create a new **Web Service** on [Render](https://render.com)
2. Connect your GitHub repository
3. Set **Root Directory** to `backend`
4. Set **Dockerfile path** to `backend/Dockerfile`
5. Add all environment variables from `.env.example` under **Environment**
6. Deploy

### Frontend → Vercel

1. Import your GitHub repo on [Vercel](https://vercel.com)
2. Set **Root Directory** to `frontend`
3. Add environment variable: `REACT_APP_API_URL = https://your-render-backend.onrender.com`
4. Deploy

---

## 🔄 CI/CD Pipeline

**File:** `.github/workflows/ci.yml`

Triggers on **Pull Requests to `main`** and **pushes to `main`**.

| Job | What it does |
|-----|--------------|
| `backend-ci` | Installs Python deps → runs `flake8` linting → validates FastAPI import |
| `frontend-ci` | Installs Node deps → ESLint → production build verification |
| `docker-build` | Builds both Docker images (validates Dockerfiles) with layer caching |
| `security-audit` | `pip-audit` for Python CVEs · `npm audit` for Node vulnerabilities |

---

## 📁 Project Structure

```
sales-insight-automator/
├── .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions CI pipeline
│
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI app, middleware registration
│   │   ├── routers/
│   │   │   └── upload.py             # POST /api/v1/upload endpoint
│   │   ├── services/
│   │   │   ├── ai_engine.py          # Gemini API integration
│   │   │   ├── email_service.py      # SMTP email delivery
│   │   │   ├── file_parser.py        # CSV/XLSX → DataFrame + stats
│   │   │   └── validator.py          # File & email validation
│   │   ├── middleware/
│   │   │   ├── rate_limit.py         # Sliding window rate limiter
│   │   │   └── security.py           # OWASP security headers
│   │   └── models/
│   │       └── schemas.py            # Pydantic request/response models
│   ├── requirements.txt
│   └── Dockerfile                    # Multi-stage, non-root production image
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js                    # Main SPA component
│   │   └── App.css                   # Distinctive editorial styling
│   ├── nginx.conf                    # Nginx config for production serving
│   ├── package.json
│   └── Dockerfile                    # Multi-stage: build → nginx serve
│
├── docker-compose.yml                # Full local stack orchestration
├── .env.example                      # Configuration template
├── .gitignore
└── README.md
```

---

## 🧪 Testing the API

### Via Swagger UI (Recommended)

Navigate to `http://localhost:8000/docs`, find the `POST /api/v1/upload` endpoint, click **Try it out**, upload the sample CSV, and enter an email.

### Via cURL

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@sales_q1_2026.csv" \
  -F "recipient_email=you@example.com"
```

### Sample Test Data (`sales_q1_2026.csv`)

```csv
Date,Product_Category,Region,Units_Sold,Unit_Price,Revenue,Status
2026-01-05,Electronics,North,150,1200,180000,Shipped
2026-01-12,Home Appliances,South,45,450,20250,Shipped
2026-01-20,Electronics,East,80,1100,88000,Delivered
2026-02-15,Electronics,North,210,1250,262500,Delivered
2026-02-28,Home Appliances,North,60,400,24000,Cancelled
2026-03-10,Electronics,West,95,1150,109250,Shipped
```

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, CSS3 (custom), Google Fonts |
| Backend | FastAPI, Uvicorn, Pydantic v2 |
| Data Processing | pandas, openpyxl |
| AI Engine | Google Gemini 1.5 Flash |
| Email | Python smtplib (SMTP/TLS) |
| Containerization | Docker (multi-stage), Docker Compose |
| Web Server | Nginx (Alpine) |
| CI/CD | GitHub Actions |
| Frontend Hosting | Vercel |
| Backend Hosting | Render |

---

## 👤 Author

**Himanshu** · AI Cloud DevOps Engineer Sprint  
Rabbitt AI · 2026
