# PassportAI — Production Deployment Guide

**Stack:** Railway (backend) + Vercel (frontend) + Supabase (DB + Storage)

---

## 1. Prerequisites

| Service | What you need |
|---------|--------------|
| **Supabase** | Free project → connection string + service role key |
| **Railway** | Account (GitHub SSO) → deploy from repo |
| **Vercel** | Account (GitHub SSO) → deploy from repo |
| **GitHub** | Repo at `BBBoring2025/passportai-mvp` |

---

## 2. Supabase Setup

1. Create a new project at [supabase.com](https://supabase.com)
2. Choose a region close to your users (e.g. `eu-central-1`)
3. Note down:
   - **Database URL** (Settings → Database → Connection string → URI)
     Format: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
   - **Supabase URL** (Settings → API → Project URL)
   - **Service Role Key** (Settings → API → service_role key)

> **Important:** Use the "Transaction" connection pooler (port 6543) for the DATABASE_URL.

---

## 3. Railway Deploy (Backend)

1. Go to [railway.com](https://railway.com) → New Project → Deploy from GitHub Repo
2. Select `BBBoring2025/passportai-mvp`
3. Set **Root Directory** to `backend`
4. Add these **Environment Variables:**

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `postgresql://postgres.[ref]:[password]@aws-0-...pooler.supabase.com:6543/postgres` |
| `APP_ENV` | `production` |
| `JWT_SECRET` | *(generate a strong random string: `openssl rand -hex 32`)* |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_EXPIRE_MINUTES` | `1440` |
| `UPLOAD_DIR` | `./uploads` |
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `CORS_ORIGINS` | `https://your-app.vercel.app` |
| `SUPABASE_URL` | `https://[ref].supabase.co` |
| `SUPABASE_SERVICE_KEY` | `eyJ...` |

5. Railway auto-detects the `Procfile` and `runtime.txt`
6. Deploy — wait for green status

### Run Migrations (one-time)

```bash
# Via Railway CLI
railway run python -m scripts.migrate_and_seed

# Or with --seed for demo data
railway run python -m scripts.migrate_and_seed --seed
```

---

## 4. Vercel Deploy (Frontend)

1. Go to [vercel.com](https://vercel.com) → Add New Project → Import from GitHub
2. Select `BBBoring2025/passportai-mvp`
3. Set **Root Directory** to `frontend`
4. Set **Framework Preset** to `Next.js`
5. Add **Environment Variable:**

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.up.railway.app/v1` |

6. Deploy

---

## 5. Post-Deploy Verification

### Backend Health Check
```bash
curl https://your-backend.up.railway.app/v1/auth/me
# Should return 401 (no token) — means API is running
```

### Frontend
- Visit `https://your-app.vercel.app`
- Should show the login page

### Demo Login (if seeded)
| Role | Email | Password |
|------|-------|----------|
| Buyer | buyer@nordic.com | demo1234 |
| Admin | admin@nordic.com | demo1234 |
| Supplier A | info@yildiz.com | demo1234 |
| Supplier B | info@ozkan.com | demo1234 |
| Supplier C | info@demir.com | demo1234 |

---

## 6. Environment Variable Reference

### Backend (Railway)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `APP_ENV` | No | `development` | `development` or `production` |
| `JWT_SECRET` | Yes | — | Secret key for JWT signing |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm |
| `JWT_EXPIRE_MINUTES` | No | `480` | Token expiry in minutes |
| `UPLOAD_DIR` | No | `./uploads` | File upload directory |
| `ANTHROPIC_API_KEY` | Yes | — | Claude API key for extraction |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated allowed origins |
| `SUPABASE_URL` | No | — | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | No | — | Supabase service role key |

### Frontend (Vercel)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API URL (e.g. `https://backend.up.railway.app/v1`) |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS errors in browser | Check `CORS_ORIGINS` env var on Railway matches your Vercel domain exactly |
| DB connection refused | Verify Supabase connection string uses port 6543 (pooler) |
| Migrations fail | Ensure `DATABASE_URL` is set before running `migrate_and_seed` |
| 500 errors on extraction | Check `ANTHROPIC_API_KEY` is set and valid |
| Frontend shows blank page | Verify `NEXT_PUBLIC_API_URL` ends with `/v1` |
