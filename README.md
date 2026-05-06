# 💰 Expense Tracker — Telegram Mini App

Full-stack Telegram Mini App for expense tracking.
**Stack**: FastAPI + Supabase + Vanilla JS + Railway

---

## 🏗️ Architecture

```
expense-tracker/
├── backend/                    # FastAPI REST API
│   ├── main.py                 # App entrypoint
│   ├── requirements.txt
│   ├── railway.toml
│   └── src/
│       ├── core/
│       │   ├── config.py       # Singleton: AppConfig
│       │   ├── logger.py       # Singleton: Logger
│       │   ├── database.py     # Supabase client
│       │   └── security.py     # JWT + Telegram auth
│       ├── models/
│       │   └── schemas.py      # Pydantic models
│       ├── repositories/
│       │   └── repositories.py # Data Access Layer
│       ├── services/
│       │   └── services.py     # Business Logic + Facade
│       ├── api/
│       │   └── routers.py      # REST endpoints
│       └── patterns/
│           └── patterns.py     # Design Patterns
│
├── frontend/                   # Telegram WebApp
│   ├── index.html              # Single-page app
│   ├── server.py               # Static file server
│   ├── railway.toml
│   └── src/
│       └── services/
│           └── services.js     # ApiService, EventBus, Builder, Strategy
│
└── sql/
    └── schema.sql              # Supabase schema (run this first!)
```

---

## 🎨 Design Patterns Implemented

| Pattern | Where | Purpose |
|---------|-------|---------|
| **Singleton** | `AppConfig`, `Logger`, `ApiService`, `EventBus` | Single instances |
| **Factory Method** | `PaymentFactory`, `NotifierFactory` | Create processors by type |
| **Builder** | `ExpenseBuilder` | Step-by-step transaction creation |
| **Observer** | `EventBus` | UI updates on transaction events |
| **Strategy** | `TransactionSorter` | Pluggable sort algorithms |
| **Facade** | `TransactionFacade` | Unified create/notify/log interface |

---

## 🚀 Deployment on Railway (Free Tier)

### Step 1 — Setup Supabase

1. Go to [supabase.com](https://supabase.com) → New Project (free)
2. Go to **SQL Editor** → paste contents of `sql/schema.sql` → Run
3. Go to **Settings → API** → copy:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_KEY`
   - `service_role` key → `SUPABASE_SERVICE_KEY`

### Step 2 — Deploy Backend on Railway

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Select your repo, set **root directory** to `backend/`
3. Add Environment Variables:
   ```
   SUPABASE_URL=https://xxx.supabase.co
   SUPABASE_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-role-key
   JWT_SECRET=some-random-long-string-change-this
   TELEGRAM_BOT_TOKEN=your-bot-token
   ```
4. Railway will auto-detect `requirements.txt` and deploy
5. Copy your Railway backend URL: `https://backend-xxx.railway.app`

### Step 3 — Deploy Frontend on Railway

1. New Service → GitHub → root directory `frontend/`
2. Add Environment Variable:
   ```
   PORT=3000
   ```
3. Edit `frontend/index.html` line with `window.ENV_API_URL`:
   Change to your backend URL:
   ```js
   this.baseURL = 'https://your-backend.railway.app/api/v1';
   ```
4. Deploy and copy frontend URL: `https://frontend-xxx.railway.app`

### Step 4 — Setup Telegram Bot

```bash
# 1. Message @BotFather on Telegram
# 2. /newbot → name it → get token
# 3. /setmenubutton → select your bot → set URL to your frontend URL
# 4. Enable Mini App:
#    /newapp → select bot → set URL to frontend
```

---

## 📡 API Reference

### Authentication
```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/telegram
GET  /api/v1/auth/me
```

### Transactions
```
GET    /api/v1/expenses              # List with filters
POST   /api/v1/expenses              # Create
GET    /api/v1/expenses/{id}         # Get by ID
PUT    /api/v1/expenses/{id}         # Update
DELETE /api/v1/expenses/{id}         # Delete
GET    /api/v1/expenses/stats        # Statistics
```

### Categories
```
GET    /api/v1/categories
POST   /api/v1/categories
PUT    /api/v1/categories/{id}
DELETE /api/v1/categories/{id}
```

### Query Parameters for GET /expenses
| Param | Values | Description |
|-------|--------|-------------|
| `type` | income, expense | Filter by type |
| `category_id` | UUID | Filter by category |
| `month` | YYYY-MM | Filter by month |
| `sort_by` | date, amount, category | Sort strategy |
| `limit` | 1-200 | Page size |
| `offset` | number | Pagination |

---

## 🧪 Example API Requests

```bash
# Register
curl -X POST https://your-api.railway.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123456"}'

# Login
curl -X POST https://your-api.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123456"}'

# Create expense (use token from login)
curl -X POST https://your-api.railway.app/api/v1/expenses \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "expense",
    "amount": 45.50,
    "currency": "USD",
    "comment": "Lunch",
    "payment_method": "card"
  }'

# Get all transactions
curl https://your-api.railway.app/api/v1/expenses \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get stats for April 2024
curl "https://your-api.railway.app/api/v1/expenses/stats?month=2024-04" \
  -H "Authorization: Bearer YOUR_TOKEN"

# View API docs
open https://your-api.railway.app/docs
```

---

## 🏠 Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Fill in your values
python main.py                    # Runs on http://localhost:8000

# Frontend
cd frontend
python -m http.server 3000        # Runs on http://localhost:3000
# Or just open index.html in browser
```

---

## 📱 Screens

| Screen | Description |
|--------|-------------|
| **Splash** | Animated intro with "Let's start" |
| **Auth** | Email/password login + Telegram SSO |
| **Home** | Balance card, income/expense chips, transaction list |
| **Overview** | Statistics chart, income vs expenses toggle, filtered list |
| **Add** | Bottom sheet: amount, category, comment, payment method |
| **Profile** | User info, settings rows, logout |

---

## 🔐 HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content (delete) |
| 401 | Unauthorized |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

---

## 📊 Database Schema (ER)

```
users ──────────────────────────────────────────────────────┐
  │                                                          │
  ├── transactions (1:N) ──── categories (1:N transactions)  │
  │         │                                                │
  │         └── expense_tags (M:N) ──── tags                │
  │                                                          │
  ├── budgets (1:N)                                          │
  ├── user_settings (1:1)                                    │
  └── categories (1:N, user-defined)                        │
```
