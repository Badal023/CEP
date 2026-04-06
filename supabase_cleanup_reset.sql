-- =====================================================
-- Gramin Santa Foundation - Supabase Cleanup + Reset
-- Purpose: Remove uploaded CMS images/data and restore defaults.
-- Run in Supabase SQL Editor.
-- =====================================================

BEGIN;

-- 1) Remove storage objects from CMS bucket (images/files)
-- Change bucket_id if your bucket name is different.
DELETE FROM storage.objects WHERE bucket_id = 'cms-assets';

-- 2) Clean CMS/content data
TRUNCATE TABLE
    about_item_images,
    about_items,
    nav_links,
    hero_slides,
    notices,
    site_content,
    homepage
RESTART IDENTITY CASCADE;

-- 3) Optional cleanup for form submissions/history (uncomment if needed)
-- TRUNCATE TABLE contacts, volunteers, payments RESTART IDENTITY CASCADE;

-- 4) Restore default homepage row
INSERT INTO homepage (title, description, hero_image, notice_text)
VALUES (
    'Shiksha Sabke Liye',
    'Supporting quality education across rural communities.',
    '',
    'Applications open for Tribal Scholarship Scheme 2026'
);

-- 5) Restore default navigation links
INSERT INTO nav_links (name, url, order_index) VALUES
('Home', '#home', 1),
('About Us', '#about', 2),
('Contact Us', 'contact.html', 3),
('Donation', 'donation.html', 4),
('Volunteer', 'volunteer.html', 5);

-- 6) Restore default notice
INSERT INTO notices (text, link_url, order_index)
VALUES ('Applications open for Tribal Scholarship Scheme 2026', '', 1);

COMMIT;

-- =====================================================
-- Notes
-- - This removes image records and storage objects in bucket cms-assets.
-- - If your bucket name differs, replace cms-assets in the DELETE statement.
-- - If your SQL role has restrictions on storage.objects, run as service role.
-- =====================================================
