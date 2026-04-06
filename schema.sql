-- =====================================================
-- Gramin Santa Foundation - Supabase Database Schema
-- Run this SQL in your Supabase SQL Editor
-- =====================================================

-- 1. Contact Us submissions
CREATE TABLE IF NOT EXISTS contacts (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'in_progress', 'resolved', 'closed')),
    admin_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Volunteer registrations
CREATE TABLE IF NOT EXISTS volunteers (
    id BIGSERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    occupation TEXT,
    skills TEXT[],
    availability TEXT NOT NULL,
    experience TEXT,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'active', 'inactive', 'rejected')),
    admin_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Payments / Donations (future scope - table ready)
CREATE TABLE IF NOT EXISTS payments (
    id BIGSERIAL PRIMARY KEY,
    donor_name TEXT,
    donor_email TEXT,
    donor_phone TEXT,
    amount DECIMAL(12,2),
    transaction_id TEXT,
    payment_method TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Admin users
CREATE TABLE IF NOT EXISTS admin_users (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'admin' CHECK (role IN ('admin', 'superadmin')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- 5. CMS content blocks
CREATE TABLE IF NOT EXISTS site_content (
    id BIGSERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    type TEXT DEFAULT 'text',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- Row Level Security (RLS) Policies
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE volunteers ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE site_content ENABLE ROW LEVEL SECURITY;

-- Allow inserts from the anon key (frontend submissions)
CREATE POLICY "Allow anonymous inserts on contacts"
    ON contacts FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY "Allow anonymous inserts on volunteers"
    ON volunteers FOR INSERT
    TO anon
    WITH CHECK (true);

-- Allow full access for authenticated/service role (backend admin)
CREATE POLICY "Allow full access for service role on contacts"
    ON contacts FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow full access for service role on volunteers"
    ON volunteers FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow full access for service role on payments"
    ON payments FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow full access for service role on admin_users"
    ON admin_users FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Also allow anon key to read/update (since Flask uses anon key)
CREATE POLICY "Allow anon select on contacts"
    ON contacts FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon update on contacts"
    ON contacts FOR UPDATE TO anon USING (true) WITH CHECK (true);

CREATE POLICY "Allow anon select on volunteers"
    ON volunteers FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon update on volunteers"
    ON volunteers FOR UPDATE TO anon USING (true) WITH CHECK (true);

CREATE POLICY "Allow anon select on payments"
    ON payments FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon all on admin_users"
    ON admin_users FOR ALL TO anon USING (true) WITH CHECK (true);

CREATE POLICY "Allow anon select on site_content"
    ON site_content FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon upsert on site_content"
    ON site_content FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Allow anon update on site_content"
    ON site_content FOR UPDATE TO anon USING (true) WITH CHECK (true);

CREATE POLICY "Allow full access for service role on site_content"
    ON site_content FOR ALL TO service_role USING (true) WITH CHECK (true);

-- =====================================================
-- Updated_at trigger function
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER contacts_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER volunteers_updated_at
    BEFORE UPDATE ON volunteers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER site_content_updated_at
    BEFORE UPDATE ON site_content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
