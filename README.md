# 💸 Expense Tracker — Telegram Mini App

> Повноцінний трекер витрат як Telegram Mini App.  
> Реалізує всі патерни з **Модуля 2** (архітектура, REST API, БД) та **Модуля 3** (ПР-8 до ПР-12).

---

## 🏗 Архітектура (Модуль 2)

```
Layered Architecture + MVC
├── Presentation Layer  → src/routes/api.js
├── Business Logic      → src/services/expenseService.js, userService.js
├── Data Access         → src/core/database.js (Supabase)
└── External Services   → Telegram WebApp API
```

## ✅ Патерни (Модуль 3)

| ПР | Що реалізовано |
|----|----------------|
| **ПР-8** | Singleton (Logger, AppConfig, Database), Factory (NotificationFactory, ResponseFactory, SortStrategyFactory), Builder (ExpenseBuilder) |
| **ПР-9** | Observer (EventBus + 3 observers), Strategy (4 sort strategies + FilterStrategies + ReportStrategies), Decorator (timer, cache, retry, withRetry) |
| **ПР-10** | Ієрархія виключень (AppError → ValidationError/BusinessError/DatabaseError), структуровані JSON-логи, валідатор ExpenseValidator |
| **ПР-11** | Рефакторинг: без magic numbers, Extract Function, константи, SRP у всіх класах |
| **ПР-12** | async/await скрізь, `Promise.allSettled` (гарантована паралельність), `runBackground` (фонові задачі), retry decorator |

---

## 🚀 РОЗГОРТАННЯ (сьогодні, за 20 хвилин)

### Крок 1 — Supabase (безкоштовна БД)

1. Йти на **https://supabase.com** → **Start your project** → Sign in with GitHub
2. **New project** → назвати `expense-tracker` → вибрати region (EU West) → Create
3. Зачекати ~2 хвилини поки БД запуститься
4. Зліва: **SQL Editor** → вставити весь вміст файлу `docs/schema.sql` → **Run**
5. Зліва: **Project Settings** → **API**:
   - Скопіювати **Project URL** (виглядає як `https://xxxx.supabase.co`)
   - Скопіювати **anon public** key

### Крок 2 — Telegram Bot

1. Написати **@BotFather** у Telegram
2. `/newbot` → ввести назву (напр. `My Expense Tracker`) → ввести username (напр. `my_expense_tracker_bot`)
3. Скопіювати **token** (виглядає як `1234567890:AAHxxxxxxx`)
4. `/newapp` → вибрати бота → ввести назву → Web App URL можна поки вказати `https://example.com` (змінимо після деплою)

### Крок 3 — Railway (безкоштовний хостинг)

1. Йти на **https://railway.app** → Sign in with GitHub
2. **New Project** → **Deploy from GitHub repo**
3. Підключити GitHub і вибрати репозиторій з цим кодом
   - Якщо немає репо: **New Project** → **Empty Project** → потім додати через CLI

#### Якщо через CLI (рекомендовано):
```bash
# Встановити Railway CLI
npm install -g @railway/cli

# Логін
railway login

# В папці з проєктом:
cd expense-tracker
railway init
railway up
```

4. У Railway dashboard → вибрати сервіс → **Variables** → додати:

```
BOT_TOKEN=ваш_токен_від_botfather
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=ваш_anon_key
NODE_ENV=production
PORT=3000
```

5. **Deploy** → зачекати ~1 хвилину
6. Скопіювати URL сервісу (напр. `https://expense-tracker-production.up.railway.app`)

### Крок 4 — Підключити Mini App до бота

1. Написати **@BotFather**
2. `/mybots` → вибрати бота → **Bot Settings** → **Menu Button** → вказати URL з Railway
3. Або використати inline кнопку:
```
/setmenubutton
```
Вказати URL: `https://your-app.up.railway.app`

### Крок 5 — Тестування

1. Відкрити бота в Telegram
2. Натиснути кнопку меню (або `/start`)
3. Має відкритись Mini App! 🎉

---

## 🔧 Локальний запуск (розробка)

```bash
# 1. Клонувати/розпакувати проєкт
cd expense-tracker

# 2. Встановити залежності
npm install

# 3. Створити .env файл
cp .env.example .env
# Відредагувати .env — вставити свої значення

# 4. Запустити
npm run dev
# або
node src/index.js

# 5. Відкрити в браузері
open http://localhost:3000
```

**Без Supabase (mock режим):** якщо `.env` не має Supabase credentials — автоматично використовується in-memory mock. Дані зберігаються до рестарту сервера.

---

## 📁 Структура проєкту

```
expense-tracker/
├── src/
│   ├── index.js                    # Entry point (Express server)
│   ├── core/
│   │   ├── config.js               # Singleton: AppConfig
│   │   ├── database.js             # Singleton: Supabase client
│   │   ├── logger.js               # Singleton: structured logger (ПР-10)
│   │   ├── decorators.js           # timer, cache, retry (ПР-9, ПР-12)
│   │   └── exceptions.js           # Exception hierarchy (ПР-10)
│   ├── services/
│   │   ├── expenseService.js       # Business logic (SRP, DIP)
│   │   └── userService.js          # User management
│   ├── routes/
│   │   └── api.js                  # REST API endpoints (ПР-5)
│   ├── observers/
│   │   └── eventBus.js             # Observer pattern (ПР-9)
│   ├── strategies/
│   │   └── sortStrategy.js         # Strategy pattern (ПР-9)
│   ├── patterns/
│   │   └── builders.js             # Factory + Builder (ПР-8)
│   └── validators/
│       └── expenseValidator.js     # Input validation (ПР-10)
├── public/
│   └── index.html                  # Telegram Mini App (all JS patterns)
├── docs/
│   └── schema.sql                  # Database schema (ПР-6)
├── .env.example
├── railway.json
└── package.json
```

---

## 🎯 REST API (Модуль 2, ПР-5)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/me` | Current user info |
| PATCH | `/api/me` | Update settings |
| GET | `/api/expenses` | Get expenses (with sort/filter) |
| POST | `/api/expenses` | Create expense |
| DELETE | `/api/expenses/:id` | Delete expense |
| GET | `/api/report` | Get spending report |
| GET | `/api/categories` | Get category list |

---

## 🧑‍💻 Multi-user support

Кожен Telegram користувач ідентифікується через `telegram_id` з `initData`.  
- Supabase Row Level Security ізолює дані між юзерами
- На бекенді: `user_id` прив'язується до кожного запиту через middleware
- Одночасно підтримується **необмежена кількість** користувачів

---

## 📚 Патерни — де знайти в коді

```
SINGLETON   → src/core/logger.js, config.js, database.js
FACTORY     → src/patterns/builders.js (NotificationFactory, ResponseFactory)
             → src/strategies/sortStrategy.js (SortStrategyFactory)
BUILDER     → src/patterns/builders.js (ExpenseBuilder)
             → public/index.html (ExpenseBuilder — frontend)
OBSERVER    → src/observers/eventBus.js (EventBus + 3 concrete observers)
             → public/index.html (EventBus + 3 observers — frontend)
STRATEGY    → src/strategies/sortStrategy.js (4 sort + 3 filter + 2 report strategies)
             → public/index.html (SortStrategies, FilterStrategies — frontend)
DECORATOR   → src/core/decorators.js (timer, cache, retry)
             → public/index.html (withTimer, withRetry — frontend)
ASYNC/AWAIT → src/services/expenseService.js (gatherSafe parallel fetch)
             → public/index.html (Promise.allSettled, async init)
EXCEPTIONS  → src/core/exceptions.js (AppError hierarchy)
VALIDATION  → src/validators/expenseValidator.js
LOGGING     → src/core/logger.js (JSON + text format, all levels)
```
