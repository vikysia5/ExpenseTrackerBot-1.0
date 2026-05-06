CREATE TABLE IF NOT EXISTS users (
  id            BIGSERIAL PRIMARY KEY,
  telegram_id   VARCHAR(50) UNIQUE NOT NULL,
  name          VARCHAR(100) NOT NULL DEFAULT 'User',
  username      VARCHAR(100),
  language_code VARCHAR(10)  DEFAULT 'en',
  currency      VARCHAR(10)  DEFAULT 'USD',
  created_at    TIMESTAMPTZ  DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_id
  ON users(telegram_id);

CREATE TABLE IF NOT EXISTS expenses (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount      DECIMAL(12,2) NOT NULL CHECK (amount > 0),
  type        VARCHAR(10)   NOT NULL DEFAULT 'expense'
                CHECK (type IN ('expense','income')),
  category    VARCHAR(30)   NOT NULL DEFAULT 'other',
  description TEXT          DEFAULT '',
  currency    VARCHAR(10)   DEFAULT 'USD',
  date        DATE          NOT NULL DEFAULT CURRENT_DATE,
  created_at  TIMESTAMPTZ   DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_id
  ON expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_date
  ON expenses(date DESC);
CREATE INDEX IF NOT EXISTS idx_expenses_user_date
  ON expenses(user_id, date DESC);

CREATE TABLE IF NOT EXISTS user_settings (
  id         BIGSERIAL PRIMARY KEY,
  user_id    BIGINT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  theme      VARCHAR(20) DEFAULT 'dark',
  language   VARCHAR(10) DEFAULT 'en',
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE users         ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses      ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "allow_all_users"         ON users;
DROP POLICY IF EXISTS "allow_all_expenses"      ON expenses;
DROP POLICY IF EXISTS "allow_all_user_settings" ON user_settings;

CREATE POLICY "allow_all_users"
  ON users         FOR ALL USING (true);
CREATE POLICY "allow_all_expenses"
  ON expenses      FOR ALL USING (true);
CREATE POLICY "allow_all_user_settings"
  ON user_settings FOR ALL USING (true);