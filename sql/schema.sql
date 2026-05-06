-- ============================================
-- Expense Tracker - Supabase SQL Schema
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id BIGINT UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_email ON users(email);

-- ============================================
-- CATEGORIES TABLE
-- ============================================
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(50) DEFAULT '📦',
    color VARCHAR(20) DEFAULT '#7C3AED',
    type VARCHAR(10) NOT NULL CHECK (type IN ('income', 'expense', 'both')),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_categories_user_id ON categories(user_id);

-- ============================================
-- TAGS TABLE
-- ============================================
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    color VARCHAR(20) DEFAULT '#7C3AED',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, name)
);

-- ============================================
-- TRANSACTIONS TABLE
-- ============================================
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('income', 'expense')),
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(10) DEFAULT 'USD',
    comment TEXT,
    payment_method VARCHAR(20) DEFAULT 'card' CHECK (payment_method IN ('cash', 'card', 'crypto')),
    transaction_date TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_category_id ON transactions(category_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date DESC);
CREATE INDEX idx_transactions_type ON transactions(type);

-- ============================================
-- EXPENSE_TAGS (M:N)
-- ============================================
CREATE TABLE expense_tags (
    transaction_id UUID REFERENCES transactions(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (transaction_id, tag_id)
);

-- ============================================
-- BUDGETS TABLE
-- ============================================
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    amount DECIMAL(15, 2) NOT NULL,
    period VARCHAR(20) DEFAULT 'monthly' CHECK (period IN ('weekly', 'monthly', 'yearly')),
    start_date DATE NOT NULL,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- USER_SETTINGS TABLE
-- ============================================
CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    currency VARCHAR(10) DEFAULT 'USD',
    language VARCHAR(10) DEFAULT 'en',
    theme VARCHAR(20) DEFAULT 'light',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    monthly_budget_limit DECIMAL(15, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- DEFAULT CATEGORIES (seed data)
-- ============================================
INSERT INTO categories (id, user_id, name, icon, color, type, is_default) VALUES
    (uuid_generate_v4(), NULL, 'Food & Dining', '🍔', '#F97316', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Transport', '🚗', '#3B82F6', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Shopping', '🛍️', '#EC4899', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Entertainment', '🎮', '#8B5CF6', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Health', '💊', '#10B981', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Bills & Utilities', '💡', '#F59E0B', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Salary', '💼', '#6366F1', 'income', TRUE),
    (uuid_generate_v4(), NULL, 'Freelance', '💻', '#7C3AED', 'income', TRUE),
    (uuid_generate_v4(), NULL, 'Investment', '📈', '#059669', 'income', TRUE),
    (uuid_generate_v4(), NULL, 'Gift', '🎁', '#DB2777', 'income', TRUE);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-create user_settings on user insert
CREATE OR REPLACE FUNCTION create_user_settings()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_settings (user_id) VALUES (NEW.id);
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER on_user_created AFTER INSERT ON users
    FOR EACH ROW EXECUTE FUNCTION create_user_settings();

-- ============================================
-- ROW LEVEL SECURITY (Supabase RLS)
-- ============================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own profile" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can CRUD own transactions" ON transactions 
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view default and own categories" ON categories 
    FOR SELECT USING (user_id IS NULL OR auth.uid() = user_id);
CREATE POLICY "Users can manage own categories" ON categories 
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own categories" ON categories 
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own categories" ON categories 
    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can CRUD own settings" ON user_settings 
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can CRUD own budgets" ON budgets 
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can CRUD own tags" ON tags 
    FOR ALL USING (auth.uid() = user_id);
