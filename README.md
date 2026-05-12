# 💰 Expense Tracker

![CI](https://github.com/vikysia5/ExpenseTrackerBot-1.0/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-59%25-green)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688)
![License](https://img.shields.io/badge/license-MIT-blue)

> Telegram Mini App для обліку доходів і витрат — без паролів, авторизація через Telegram ID.

## Зміст

- [Опис](#опис)
- [Технологічний стек](#технологічний-стек)
- [Швидкий старт](#швидкий-старт)
- [API Документація](#api-документація)
- [Тестування](#тестування)
- [Структура проєкту](#структура-проєкту)
- [Патерни проектування](#патерни-проектування)
- [База даних](#база-даних)
- [Ліцензія](#ліцензія)

## Опис

Expense Tracker — повноцінний Telegram Mini App для відстеження особистих фінансів. Користувач входить через Telegram без реєстрації та паролів, записує доходи й витрати за категоріями, переглядає статистику у вигляді графіків та отримує сповіщення після кожної транзакції.

**Ключові можливості:**

- 🔐 Авторизація виключно через Telegram ID — жодних паролів
- 💳 Запис транзакцій з категоріями, коментарями та типом оплати
- 📊 Тижневий графік доходів і витрат з фільтрацією
- 🔔 Фонові Telegram-сповіщення через BackgroundTasks
- 🛡️ Row Level Security — кожен бачить лише свої дані

## Технологічний стек

| Компонент   | Технологія          | Версія  |
|-------------|---------------------|---------|
| Backend     | Python / FastAPI    | 3.12 / 0.111 |
| База даних  | Supabase (PostgreSQL) | 16    |
| Frontend    | Vanilla JS / TG SDK | —       |
| Тестування  | pytest + pytest-cov | 9.x     |
| CI/CD       | GitHub Actions      | —       |
| Контейнери  | Docker              | 25.x    |
| Хостинг     | Railway.app         | —       |

## Швидкий старт

### Вимоги

- Docker 25+
- Акаунт на [supabase.com](https://supabase.com) (безкоштовно)
- Акаунт на [railway.app](https://railway.app) (безкоштовно)

### Запуск за 3 команди

```bash
git clone https://github.com/vikysia5/ExpenseTrackerBot-1.0.git
cd ExpenseTrackerBot-1.0
cp backend/.env.example backend/.env  # заповни змінні
docker-compose up -d
```

Застосунок доступний на `http://localhost:8000`

Swagger UI: `http://localhost:8000/docs`

### Запуск без Docker (розробка)

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

### Змінні середовища

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
JWT_SECRET=your-random-secret
TELEGRAM_BOT_TOKEN=your-bot-token
```

## API Документація

Повна інтерактивна документація: `http://localhost:8000/docs` (Swagger UI)

| Метод  | URL                        | Опис                    |
|--------|----------------------------|-------------------------|
| POST   | /api/v1/auth/telegram      | Вхід через Telegram     |
| GET    | /api/v1/auth/me            | Поточний користувач     |
| GET    | /api/v1/expenses           | Список транзакцій       |
| POST   | /api/v1/expenses           | Створити транзакцію     |
| PUT    | /api/v1/expenses/{id}      | Оновити транзакцію      |
| DELETE | /api/v1/expenses/{id}      | Видалити транзакцію     |
| GET    | /api/v1/expenses/stats     | Статистика              |
| GET    | /api/v1/categories         | Список категорій        |
| POST   | /api/v1/categories         | Створити категорію      |

## Тестування

```bash
cd backend
source .venv/bin/activate
python -m pytest --cov=src -v
```

Поточне покриття: **59%** (мінімум: 50%)

Структура тестів:

```
tests/
├── unit/
│   ├── test_validators.py   # 10 тестів Pydantic-схем
│   ├── test_services.py     # 5 тестів бізнес-логіки з Mock
│   └── test_balance.py      # 3 TDD-тести функції calculate_balance
├── integration/
│   └── test_repository.py   # 6 інтеграційних тестів репозиторію
├── test_exceptions.py       # 12 тестів обробки помилок
└── conftest.py              # спільні фікстури
```

## Структура проєкту

```
expense-tracker/
├── backend/
│   ├── main.py                  # Точка входу FastAPI
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── railway.toml
│   └── src/
│       ├── api/                 # REST роутери
│       ├── core/                # Config, Logger, Security, DB
│       ├── models/              # Pydantic схеми
│       ├── repositories/        # Data Access Layer
│       ├── services/            # Business Logic + Facade
│       ├── patterns/            # GoF патерни
│       └── validators/          # Валідація даних
├── frontend/
│   ├── index.html               # Single-page Telegram WebApp
│   ├── server.py                # Статичний сервер
│   └── src/services/services.js # ApiService, EventBus, Builder
├── sql/
│   └── schema.sql               # Supabase схема (7 таблиць)
├── .github/workflows/ci.yml     # GitHub Actions CI/CD
└── docker-compose.yml
```

## Патерни проектування

| Патерн          | Де реалізовано                        | Призначення                          |
|-----------------|---------------------------------------|--------------------------------------|
| **Singleton**   | `AppConfig`, `Logger`, `EventBus`     | Один екземпляр на весь додаток       |
| **Factory**     | `PaymentFactory`, `NotifierFactory`   | Створення процесорів за типом        |
| **Builder**     | `ExpenseBuilder`                      | Покрокове створення транзакції       |
| **Observer**    | `EventBus`                            | Оновлення UI при змінах              |
| **Strategy**    | `TransactionSorter`                   | Сортування за датою/сумою/категорією |
| **Facade**      | `TransactionFacade`                   | Єдиний інтерфейс create+notify+log   |

Декоратори застосовані до DB-функцій:

- `@timer` — вимірює час запиту до Supabase
- `@log_call` — логує аргументи та результат
- `@retry(times=3)` — 3 спроби при помилці мережі

## База даних

```
users ─────────────────────────────────────┐
  ├── transactions (1:N)                   │
  │     └── expense_tags (M:N) ── tags     │
  ├── categories (1:N)                     │
  ├── budgets (1:N)                        │
  └── user_settings (1:1)                  │
```

Суpabase RLS увімкнено — кожен користувач бачить лише свої дані.

## Ліцензія

MIT © 2026 Viktoriia Chuhunnykova
