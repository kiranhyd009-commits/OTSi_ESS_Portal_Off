-- ============================================================
-- OTSI ESS Portal - Official Company Holidays Calendar 2026
-- Schema: public
-- Includes all 14 official OTSI India holidays & standard US holidays
-- ============================================================

CREATE TABLE IF NOT EXISTS holidays (
    id SERIAL PRIMARY KEY,
    holiday_date DATE NOT NULL,
    occasion VARCHAR(150) NOT NULL,
    remark VARCHAR(255) DEFAULT 'All Locations',
    region VARCHAR(50) DEFAULT 'India',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(holiday_date, occasion)
);

-- Performance index
CREATE INDEX IF NOT EXISTS idx_holidays_date ON holidays(holiday_date);
CREATE INDEX IF NOT EXISTS idx_holidays_region ON holidays(region);

-- Allow frontend portal and backend scripts to read & write holidays
ALTER TABLE IF EXISTS holidays DISABLE ROW LEVEL SECURITY;

-- ─────────────────────────────────────────────────────────────
-- 1. SEED OTSI INDIA OFFICIAL HOLIDAYS 2026 (14 Days)
-- ─────────────────────────────────────────────────────────────

INSERT INTO holidays (holiday_date, occasion, remark, region) VALUES
    ('2026-01-01', 'New Year Day', 'All Locations', 'India'),
    ('2026-01-14', 'Sankranti / Pongal', 'All Locations excluding Bangalore', 'India'),
    ('2026-01-15', 'Makara Sankranti', 'Only Bangalore', 'India'),
    ('2026-01-26', 'Republic Day', 'All Locations', 'India'),
    ('2026-03-03', 'Holi', 'Only Delhi', 'India'),
    ('2026-03-19', 'Ugadi', 'All Locations excluding Delhi', 'India'),
    ('2026-05-01', 'Budha Purnima / May Day', 'All Locations excluding Bangalore', 'India'),
    ('2026-05-27', 'Eidul Azha (Bakrid)', 'All Locations', 'India'),
    ('2026-09-14', 'Vinayaka Chavithi', 'All Locations', 'India'),
    ('2026-10-02', 'Mahatma Gandhi Jayanthi', 'All Locations', 'India'),
    ('2026-10-20', 'Vijaya Dasami (Dussehra)', 'All Locations excluding Bangalore', 'India'),
    ('2026-10-21', 'Following Day of Vijaya Dasami', 'Only Bangalore', 'India'),
    ('2026-11-10', 'Balipadyami', 'Only Bangalore', 'India'),
    ('2026-12-25', 'Christmas', 'All Locations', 'India')
ON CONFLICT (holiday_date, occasion) DO UPDATE SET
    remark = EXCLUDED.remark,
    region = EXCLUDED.region,
    updated_at = CURRENT_TIMESTAMP;

-- ─────────────────────────────────────────────────────────────
-- 2. SEED OTSI US OFFICIAL HOLIDAYS 2026
-- ─────────────────────────────────────────────────────────────

INSERT INTO holidays (holiday_date, occasion, remark, region) VALUES
    ('2026-01-01', 'New Year''s Day', 'All US Locations', 'US'),
    ('2026-01-19', 'Martin Luther King Jr. Day', 'All US Locations', 'US'),
    ('2026-05-25', 'Memorial Day', 'All US Locations', 'US'),
    ('2026-06-19', 'Juneteenth National Independence Day', 'All US Locations', 'US'),
    ('2026-07-03', 'Independence Day (Observed)', 'All US Locations', 'US'),
    ('2026-09-07', 'Labor Day', 'All US Locations', 'US'),
    ('2026-11-26', 'Thanksgiving Day', 'All US Locations', 'US'),
    ('2026-11-27', 'Day After Thanksgiving', 'All US Locations', 'US'),
    ('2026-12-25', 'Christmas Day', 'All US Locations', 'US')
ON CONFLICT (holiday_date, occasion) DO UPDATE SET
    remark = EXCLUDED.remark,
    region = EXCLUDED.region,
    updated_at = CURRENT_TIMESTAMP;
