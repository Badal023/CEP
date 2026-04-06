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

-- 6. Structured homepage content
CREATE TABLE IF NOT EXISTS homepage (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    hero_image TEXT,
    notice_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Dynamic about section items
CREATE TABLE IF NOT EXISTS about_items (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    image_url TEXT,
    order_index INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Navigation links (multi-item)
CREATE TABLE IF NOT EXISTS nav_links (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    order_index INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. Hero slides (multi-item)
CREATE TABLE IF NOT EXISTS hero_slides (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    image_url TEXT NOT NULL,
    order_index INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. Notice messages (multi-item)
CREATE TABLE IF NOT EXISTS notices (
    id BIGSERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    link_url TEXT,
    order_index INT DEFAULT 1,
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
ALTER TABLE homepage ENABLE ROW LEVEL SECURITY;
ALTER TABLE about_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE nav_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE hero_slides ENABLE ROW LEVEL SECURITY;
ALTER TABLE notices ENABLE ROW LEVEL SECURITY;

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

CREATE POLICY "Allow anon select on homepage"
    ON homepage FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon insert on homepage"
    ON homepage FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Allow anon update on homepage"
    ON homepage FOR UPDATE TO anon USING (true) WITH CHECK (true);

CREATE POLICY "Allow full access for service role on homepage"
    ON homepage FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow anon select on about_items"
    ON about_items FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon insert on about_items"
    ON about_items FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Allow anon update on about_items"
    ON about_items FOR UPDATE TO anon USING (true) WITH CHECK (true);

CREATE POLICY "Allow anon delete on about_items"
    ON about_items FOR DELETE TO anon USING (true);

CREATE POLICY "Allow full access for service role on about_items"
    ON about_items FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow anon select on nav_links"
    ON nav_links FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon insert on nav_links"
    ON nav_links FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Allow anon delete on nav_links"
    ON nav_links FOR DELETE TO anon USING (true);

CREATE POLICY "Allow full access for service role on nav_links"
    ON nav_links FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow anon select on hero_slides"
    ON hero_slides FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon insert on hero_slides"
    ON hero_slides FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Allow anon delete on hero_slides"
    ON hero_slides FOR DELETE TO anon USING (true);

CREATE POLICY "Allow full access for service role on hero_slides"
    ON hero_slides FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow anon select on notices"
    ON notices FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon insert on notices"
    ON notices FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Allow anon delete on notices"
    ON notices FOR DELETE TO anon USING (true);

CREATE POLICY "Allow full access for service role on notices"
    ON notices FOR ALL TO service_role USING (true) WITH CHECK (true);

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

CREATE TRIGGER homepage_updated_at
    BEFORE UPDATE ON homepage
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER about_items_updated_at
    BEFORE UPDATE ON about_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER nav_links_updated_at
    BEFORE UPDATE ON nav_links
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER hero_slides_updated_at
    BEFORE UPDATE ON hero_slides
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER notices_updated_at
    BEFORE UPDATE ON notices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
