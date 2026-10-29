-- ============================================================
-- OTSI Attendance Portal - 250 Employee Organizational Structure
-- Complete Unified Schema & Seed Data (Supabase / PostgreSQL)
-- Schema: public
-- ============================================================

-- ─────────────────────────────────────────────────────────
-- 0. CLEAN RESET & RESTART ALL IDENTITY SEQUENCES FROM 1
-- ─────────────────────────────────────────────────────────

TRUNCATE TABLE 
    attendance_logs, 
    leave_applications, 
    timesheet_entries, 
    timesheets, 
    support_tickets, 
    notifications, 
    audit_logs, 
    password_history, 
    leave_balance, 
    employees, 
    teams, 
    departments,
    holidays
RESTART IDENTITY CASCADE;

ALTER SEQUENCE IF EXISTS employees_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS attendance_logs_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS leave_balance_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS departments_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS teams_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS holidays_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS leave_applications_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS timesheets_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS timesheet_entries_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS support_tickets_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS notifications_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS audit_logs_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS password_history_id_seq RESTART WITH 1;

-- ─────────────────────────────────────────────────────────
-- 1. CREATE CORE TABLES
-- ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    manager_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    department_name VARCHAR(150),
    team_lead_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, department_name)
);

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    designation VARCHAR(100),
    department VARCHAR(100),
    team VARCHAR(100),
    manager_id VARCHAR(50),
    manager_name VARCHAR(150),
    phone VARCHAR(20),
    date_of_joining DATE,
    role VARCHAR(20) DEFAULT 'employee' CHECK (role IN ('employee', 'hr', 'admin')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'on_leave')),
    is_active BOOLEAN DEFAULT TRUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    lockout_until TIMESTAMP,
    mfa_enabled BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS leave_balance (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL UNIQUE REFERENCES employees(employee_id) ON DELETE CASCADE,
    casual_leave INT DEFAULT 12,
    sick_leave INT DEFAULT 8,
    earned_leave DECIMAL(4, 1) DEFAULT 20.0,
    bereavement_leave INT DEFAULT 3,
    marriage_leave INT DEFAULT 0,
    lop_leave INT DEFAULT 0,
    last_reset_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance_logs (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    check_in_time TIMESTAMP,
    check_out_time TIMESTAMP,
    check_in_latitude FLOAT,
    check_in_longitude FLOAT,
    check_in_location VARCHAR(255),
    is_wfh BOOLEAN DEFAULT FALSE,
    working_hours DECIMAL(5, 2),
    status VARCHAR(20) DEFAULT 'absent' CHECK (status IN ('present', 'absent', 'wfh', 'late', 'half_day')),
    is_late BOOLEAN DEFAULT FALSE,
    location_verified BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, attendance_date)
);

CREATE TABLE IF NOT EXISTS leave_applications (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    leave_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    number_of_days DECIMAL(3, 1),
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled')),
    approved_by VARCHAR(50),
    approval_date TIMESTAMP,
    approval_comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS timesheets (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'submitted', 'approved', 'rejected')),
    total_hours DECIMAL(5, 2),
    submitted_date TIMESTAMP,
    approved_by VARCHAR(50),
    approved_date TIMESTAMP,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, week_start_date)
);

CREATE TABLE IF NOT EXISTS timesheet_entries (
    id SERIAL PRIMARY KEY,
    timesheet_id INT NOT NULL REFERENCES timesheets(id) ON DELETE CASCADE,
    entry_date DATE NOT NULL,
    project_name VARCHAR(200),
    task_description VARCHAR(500),
    hours_worked DECIMAL(3, 1) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    employee_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    priority VARCHAR(10) DEFAULT 'p3' CHECK (priority IN ('p1', 'p2', 'p3')),
    subject VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    assigned_to VARCHAR(50),
    resolution TEXT,
    resolved_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    title VARCHAR(200),
    message TEXT,
    type VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    action_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50),
    action VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id INT,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS password_history (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

-- ─────────────────────────────────────────────────────────
-- 2. PERFORMANCE INDEXES & PERMISSIONS
-- ─────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_employees_mgr ON employees(manager_id);
CREATE INDEX IF NOT EXISTS idx_employees_dept ON employees(department);
CREATE INDEX IF NOT EXISTS idx_employees_team ON employees(team);
CREATE INDEX IF NOT EXISTS idx_attendance_logs_emp_date ON attendance_logs(employee_id, attendance_date);
CREATE INDEX IF NOT EXISTS idx_leave_apps_emp ON leave_applications(employee_id);
CREATE INDEX IF NOT EXISTS idx_timesheets_emp ON timesheets(employee_id);
CREATE INDEX IF NOT EXISTS idx_holidays_date ON holidays(holiday_date);

ALTER TABLE IF EXISTS departments DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS teams DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS employees DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS leave_balance DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS attendance_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS leave_applications DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS timesheets DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS timesheet_entries DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS support_tickets DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS password_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS holidays DISABLE ROW LEVEL SECURITY;

-- ─────────────────────────────────────────────────────────
-- 3. SEED DEPARTMENTS & TEAMS
-- ─────────────────────────────────────────────────────────
ALTER TABLE IF EXISTS teams ADD COLUMN IF NOT EXISTS department_name VARCHAR(150);
ALTER TABLE IF EXISTS teams ADD COLUMN IF NOT EXISTS department_id INT;

INSERT INTO departments (name) VALUES ('Application Engineering') ON CONFLICT (name) DO NOTHING;
INSERT INTO departments (name) VALUES ('Data & Analytics') ON CONFLICT (name) DO NOTHING;
INSERT INTO departments (name) VALUES ('Digital Transformation') ON CONFLICT (name) DO NOTHING;
INSERT INTO departments (name) VALUES ('Executive Leadership & Governance') ON CONFLICT (name) DO NOTHING;
INSERT INTO departments (name) VALUES ('Finance, Compliance & Administration') ON CONFLICT (name) DO NOTHING;
INSERT INTO departments (name) VALUES ('Human Resources') ON CONFLICT (name) DO NOTHING;
INSERT INTO departments (name) VALUES ('IT Infrastructure & Cloud') ON CONFLICT (name) DO NOTHING;
INSERT INTO departments (name) VALUES ('Operations & PMO') ON CONFLICT (name) DO NOTHING;
INSERT INTO departments (name) VALUES ('Quality Assurance & Testing') ON CONFLICT (name) DO NOTHING;
INSERT INTO departments (name) VALUES ('Sales & Business Development') ON CONFLICT (name) DO NOTHING;

INSERT INTO teams (name, department_id, department_name)
SELECT t.name, d.id, t.dept_name
FROM (VALUES
    ('AI & Machine Learning', 'Data & Analytics'),
    ('ALM & Polarion Practice', 'Application Engineering'),
    ('APAC & MENA Operations Leadership', 'Executive Leadership & Governance'),
    ('APAC Commercial Sales Leadership', 'Executive Leadership & Governance'),
    ('APAC Public Sector Sales Leadership', 'Executive Leadership & Governance'),
    ('Architecture & Technology Excellence', 'Executive Leadership & Governance'),
    ('Automation & Performance QA', 'Quality Assurance & Testing'),
    ('BI & Reporting', 'Data & Analytics'),
    ('Big Data Engineering', 'Data & Analytics'),
    ('Board of Directors', 'Executive Leadership & Governance'),
    ('Cloud Data Platforms', 'Data & Analytics'),
    ('Cloud Infrastructure & Ops', 'IT Infrastructure & Cloud'),
    ('Cloud Solutions Delivery', 'Data & Analytics'),
    ('Commercial Enterprise Sales', 'Sales & Business Development'),
    ('Data & Analytics Leadership', 'Data & Analytics'),
    ('Data Practice Center of Excellence', 'Data & Analytics'),
    ('Digital Transformation CoE', 'Digital Transformation'),
    ('Embedded & IoT Solutions', 'Application Engineering'),
    ('Engineering Leadership', 'Application Engineering'),
    ('Enterprise Systems QA', 'Quality Assurance & Testing'),
    ('Executive Committee', 'Executive Leadership & Governance'),
    ('Finance & Statutory Compliance', 'Finance, Compliance & Administration'),
    ('Frontend & Mobile Apps', 'Application Engineering'),
    ('Full Stack Web & Python', 'Application Engineering'),
    ('Functional & Regression QA', 'Quality Assurance & Testing'),
    ('Global Delivery Leadership', 'Executive Leadership & Governance'),
    ('HR Leadership', 'Executive Leadership & Governance'),
    ('HR Operations & People Management', 'Human Resources'),
    ('IT Operations Leadership', 'IT Infrastructure & Cloud'),
    ('Mobile & Web QA', 'Quality Assurance & Testing'),
    ('Network Security & Telecom', 'IT Infrastructure & Cloud'),
    ('Public Sector Sales', 'Sales & Business Development'),
    ('QA Practice Leadership', 'Quality Assurance & Testing'),
    ('Resource & Logistics Operations', 'Operations & PMO'),
    ('Resource Management & Staffing', 'Human Resources'),
    ('Strategy & Cloud Advisory', 'Digital Transformation'),
    ('Talent Acquisition & Technical Recruiting', 'Human Resources')
) AS t(name, dept_name)
JOIN departments d ON d.name = t.dept_name
ON CONFLICT DO NOTHING;

-- ─────────────────────────────────────────────────────────
-- 3.5 SEED OFFICIAL OTSI COMPANY HOLIDAYS 2026
-- ─────────────────────────────────────────────────────────

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
    ('2026-12-25', 'Christmas', 'All Locations', 'India'),
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

-- ─────────────────────────────────────────────────────────
-- 4. SEED 257 EMPLOYEES (Password: M@llem5831!)
-- ─────────────────────────────────────────────────────────
-- Clear any previous preliminary seed records to prevent email/ID conflicts
TRUNCATE TABLE employees CASCADE;

INSERT INTO employees (employee_id, email, full_name, designation, department, team, manager_id, manager_name, phone, role, status, password_hash, date_of_joining) VALUES
    ('OTSI0001', 'admin.otsi@otsi-usa.com', 'Rajesh K.', 'Chairman & Founder / President', 'Executive Leadership & Governance', 'Board of Directors', NULL, NULL, '+91 98490 00001', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2015-01-10'),
    ('EMP1001', 'ceo.otsi@otsi-usa.com', 'Chandra Sekhar M.', 'Chief Executive Officer (CEO)', 'Executive Leadership & Governance', 'Executive Committee', 'OTSI0001', 'Rajesh K.', '+91 98490 00002', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2016-03-15'),
    ('EMP1000', 'kiran.us009@gmail.com', 'Ravi Kiran V.', 'Senior Vice President – Global Delivery', 'Executive Leadership & Governance', 'Global Delivery Leadership', 'EMP1001', 'Chandra Sekhar M.', '+91 98490 00003', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2017-02-01'),
    ('EMP1003', 'suresh.nambiar@otsi-usa.com', 'Suresh Nambiar', 'Sr. Vice President – Government & Public Sector Sales, APAC', 'Executive Leadership & Governance', 'APAC Public Sector Sales Leadership', 'EMP1001', 'Chandra Sekhar M.', '+91 98490 00004', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2017-06-12'),
    ('EMP1004', 'vikram.rao@otsi-usa.com', 'Vikramaditya Rao', 'Sr. Vice President – Client Partner & Commercial Sales, APAC', 'Executive Leadership & Governance', 'APAC Commercial Sales Leadership', 'EMP1001', 'Chandra Sekhar M.', '+91 98490 00005', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2017-08-20'),
    ('EMP1005', 'subhashini.r@otsi.co.in', 'Subhashini R.', 'Associate Vice President – Operations & Finance, APAC & MENA', 'Executive Leadership & Governance', 'APAC & MENA Operations Leadership', 'EMP1001', 'Chandra Sekhar M.', '+91 98490 00006', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2018-01-15'),
    ('EMP1006', 'priyanka.sengupta@otsi.co.in', 'Priyanka Sengupta', 'Sr. Director – Human Resources, APAC & MENA', 'Executive Leadership & Governance', 'HR Leadership', 'EMP1001', 'Chandra Sekhar M.', '+91 98490 00007', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2018-04-10'),
    ('EMP1007', 'anand.vardhan@otsi.co.in', 'Anand Vardhan', 'Principal Architect – Microsoft', 'Executive Leadership & Governance', 'Architecture & Technology Excellence', 'EMP1001', 'Chandra Sekhar M.', '+91 98490 00008', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2018-07-01'),
    ('EMP1008', 'manoj.kumar@otsi.co.in', 'Manoj Kumar K.', 'Sr. Delivery Director – Data & Analytics', 'Data & Analytics', 'Data & Analytics Leadership', 'EMP1000', 'Ravi Kiran V.', '+91 98490 00009', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2018-09-15'),
    ('EMP1009', 'naveen.reddy@otsi.co.in', 'Naveen Reddy T.', 'Sr. Delivery Director – Big Data & Analytics', 'Data & Analytics', 'Big Data Engineering', 'EMP1000', 'Ravi Kiran V.', '+91 98490 00010', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2018-11-01'),
    ('EMP1010', 'deepak.sharma@otsi.co.in', 'Deepak Sharma', 'Sr. Delivery Director – Big Data & Cloud Solutions', 'Data & Analytics', 'Cloud Solutions Delivery', 'EMP1000', 'Ravi Kiran V.', '+91 98490 00011', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2019-01-10'),
    ('EMP1011', 'kavitha.swaminathan@otsi.co.in', 'Kavitha Swaminathan', 'Practice Director – Big Data & Analytics', 'Data & Analytics', 'Data Practice Center of Excellence', 'EMP1000', 'Ravi Kiran V.', '+91 98490 00012', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2019-03-20'),
    ('EMP1012', 'raghavendra.prasad@otsi.co.in', 'Raghavendra Prasad', 'Practice Director – Quality Assurance', 'Quality Assurance & Testing', 'QA Practice Leadership', 'EMP1000', 'Ravi Kiran V.', '+91 98490 00013', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2019-05-15'),
    ('EMP1013', 'siddharth.mehta@otsi.co.in', 'Siddharth Mehta', 'Practice Director – Digital Transformation', 'Digital Transformation', 'Digital Transformation CoE', 'EMP1000', 'Ravi Kiran V.', '+91 98490 00014', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2019-07-01'),
    ('EMP1014', 'sunil.chander@otsi.co.in', 'Sunil Chander', 'Director – IT Infrastructure & Cloud', 'IT Infrastructure & Cloud', 'IT Operations Leadership', 'EMP1000', 'Ravi Kiran V.', '+91 98490 00015', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2019-09-01'),
    ('EMP1015', 'venkat.ramana@otsi.co.in', 'Venkat Ramana M.', 'Delivery Director – Application Engineering', 'Application Engineering', 'Engineering Leadership', 'EMP1000', 'Ravi Kiran V.', '+91 98490 00016', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2019-10-15'),
    ('EMP1016', 'tarun.nair@otsi.co.in', 'Tarun Nair', 'Sr. Data Scientist', 'Data & Analytics', 'BI & Reporting', 'EMP1008', 'Manoj Kumar K.', '+91 98490 01016', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-05-11'),
    ('EMP1017', 'usha.kulkarni@otsi.co.in', 'Usha Kulkarni', 'Sr. Data Scientist', 'Data & Analytics', 'Big Data Engineering', 'EMP1009', 'Naveen Reddy T.', '+91 98490 01017', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-06-17'),
    ('EMP1018', 'varun.pillai@otsi.co.in', 'Varun Pillai', 'Sr. Data Scientist', 'Data & Analytics', 'Cloud Data Platforms', 'EMP1010', 'Deepak Sharma', '+91 98490 01018', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-07-24'),
    ('EMP1019', 'yash.joshi@otsi.co.in', 'Yash Joshi', 'Sr. Data Scientist', 'Data & Analytics', 'AI & Machine Learning', 'EMP1011', 'Kavitha Swaminathan', '+91 98490 01019', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-08-30'),
    ('EMP1020', 'arun.rao@otsi.co.in', 'Arun Rao', 'Sr. Data Scientist', 'Data & Analytics', 'BI & Reporting', 'EMP1008', 'Manoj Kumar K.', '+91 98490 01020', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-10-06'),
    ('EMP1021', 'bhavana.patel@otsi.co.in', 'Bhavana Patel', 'Sr. Data Scientist', 'Data & Analytics', 'Big Data Engineering', 'EMP1009', 'Naveen Reddy T.', '+91 98490 01021', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-11-12'),
    ('EMP1022', 'chetan.nair@otsi.co.in', 'Chetan Nair', 'Data Scientist', 'Data & Analytics', 'Cloud Data Platforms', 'EMP1010', 'Deepak Sharma', '+91 98490 01022', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-12-19'),
    ('EMP1023', 'divya.kulkarni@otsi.co.in', 'Divya Kulkarni', 'Data Scientist', 'Data & Analytics', 'AI & Machine Learning', 'EMP1011', 'Kavitha Swaminathan', '+91 98490 01023', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-01-25'),
    ('EMP1024', 'ganesh.pillai@otsi.co.in', 'Ganesh Pillai', 'Data Scientist', 'Data & Analytics', 'BI & Reporting', 'EMP1008', 'Manoj Kumar K.', '+91 98490 01024', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-03-03'),
    ('EMP1025', 'harish.joshi@otsi.co.in', 'Harish Joshi', 'Data Scientist', 'Data & Analytics', 'Big Data Engineering', 'EMP1009', 'Naveen Reddy T.', '+91 98490 01025', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-04-09'),
    ('EMP1026', 'ishita.rao@otsi.co.in', 'Ishita Rao', 'Data Scientist', 'Data & Analytics', 'Cloud Data Platforms', 'EMP1010', 'Deepak Sharma', '+91 98490 01026', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-05-16'),
    ('EMP1027', 'jayant.patel@otsi.co.in', 'Jayant Patel', 'Data Scientist', 'Data & Analytics', 'AI & Machine Learning', 'EMP1011', 'Kavitha Swaminathan', '+91 98490 01027', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-06-22'),
    ('EMP1028', 'karthik.nair@otsi.co.in', 'Karthik Nair', 'Data Scientist', 'Data & Analytics', 'BI & Reporting', 'EMP1008', 'Manoj Kumar K.', '+91 98490 01028', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-02-06'),
    ('EMP1029', 'lakshmi.kulkarni@otsi.co.in', 'Lakshmi Kulkarni', 'Data Scientist', 'Data & Analytics', 'Big Data Engineering', 'EMP1009', 'Naveen Reddy T.', '+91 98490 01029', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-03-14'),
    ('EMP1030', 'madhav.pillai@otsi.co.in', 'Madhav Pillai', 'Senior Data Analyst', 'Data & Analytics', 'Cloud Data Platforms', 'EMP1010', 'Deepak Sharma', '+91 98490 01030', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-04-20'),
    ('EMP1031', 'nandini.joshi@otsi.co.in', 'Nandini Joshi', 'Senior Data Analyst', 'Data & Analytics', 'AI & Machine Learning', 'EMP1011', 'Kavitha Swaminathan', '+91 98490 01031', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-05-27'),
    ('EMP1032', 'omkar.rao@otsi.co.in', 'Omkar Rao', 'Senior Data Analyst', 'Data & Analytics', 'BI & Reporting', 'EMP1008', 'Manoj Kumar K.', '+91 98490 01032', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-07-03'),
    ('EMP1033', 'pooja.patel@otsi.co.in', 'Pooja Patel', 'Senior Data Analyst', 'Data & Analytics', 'Big Data Engineering', 'EMP1009', 'Naveen Reddy T.', '+91 98490 01033', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-08-09'),
    ('EMP1034', 'rajiv.nair@otsi.co.in', 'Rajiv Nair', 'Senior Data Analyst', 'Data & Analytics', 'Cloud Data Platforms', 'EMP1010', 'Deepak Sharma', '+91 98490 01034', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-09-15'),
    ('EMP1035', 'sneha.kulkarni@otsi.co.in', 'Sneha Kulkarni', 'Senior Data Analyst', 'Data & Analytics', 'AI & Machine Learning', 'EMP1011', 'Kavitha Swaminathan', '+91 98490 01035', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-10-22'),
    ('EMP1036', 'tarun.pillai@otsi.co.in', 'Tarun Pillai', 'Senior Data Analyst', 'Data & Analytics', 'BI & Reporting', 'EMP1008', 'Manoj Kumar K.', '+91 98490 01036', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-11-28'),
    ('EMP1037', 'usha.joshi@otsi.co.in', 'Usha Joshi', 'Senior Data Analyst', 'Data & Analytics', 'Big Data Engineering', 'EMP1009', 'Naveen Reddy T.', '+91 98490 01037', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-01-04'),
    ('EMP1038', 'varun.rao@otsi.co.in', 'Varun Rao', 'Data Analyst', 'Data & Analytics', 'Cloud Data Platforms', 'EMP1010', 'Deepak Sharma', '+91 98490 01038', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-02-10'),
    ('EMP1039', 'yash.patel@otsi.co.in', 'Yash Patel', 'Data Analyst', 'Data & Analytics', 'AI & Machine Learning', 'EMP1011', 'Kavitha Swaminathan', '+91 98490 01039', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-03-19'),
    ('EMP1040', 'arun.nair@otsi.co.in', 'Arun Nair', 'Data Analyst', 'Data & Analytics', 'BI & Reporting', 'EMP1008', 'Manoj Kumar K.', '+91 98490 01040', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-04-25'),
    ('EMP1041', 'bhavana.kulkarni@otsi.co.in', 'Bhavana Kulkarni', 'Data Analyst', 'Data & Analytics', 'Big Data Engineering', 'EMP1009', 'Naveen Reddy T.', '+91 98490 01041', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-06-01'),
    ('EMP1042', 'chetan.pillai@otsi.co.in', 'Chetan Pillai', 'Data Analyst', 'Data & Analytics', 'Cloud Data Platforms', 'EMP1010', 'Deepak Sharma', '+91 98490 01042', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-07-08'),
    ('EMP1043', 'divya.joshi@otsi.co.in', 'Divya Joshi', 'Data Analyst', 'Data & Analytics', 'AI & Machine Learning', 'EMP1011', 'Kavitha Swaminathan', '+91 98490 01043', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-08-14'),
    ('EMP1044', 'ganesh.rao@otsi.co.in', 'Ganesh Rao', 'Data Analyst', 'Data & Analytics', 'BI & Reporting', 'EMP1008', 'Manoj Kumar K.', '+91 98490 01044', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-09-20'),
    ('EMP1045', 'harish.patel@otsi.co.in', 'Harish Patel', 'Data Analyst', 'Data & Analytics', 'Big Data Engineering', 'EMP1009', 'Naveen Reddy T.', '+91 98490 01045', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-10-27'),
    ('EMP1046', 'ishita.nair@otsi.co.in', 'Ishita Nair', 'SAS Programmer', 'Data & Analytics', 'Cloud Data Platforms', 'EMP1010', 'Deepak Sharma', '+91 98490 01046', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-12-03'),
    ('EMP1047', 'jayant.kulkarni@otsi.co.in', 'Jayant Kulkarni', 'SAS Programmer', 'Data & Analytics', 'AI & Machine Learning', 'EMP1011', 'Kavitha Swaminathan', '+91 98490 01047', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-01-09'),
    ('EMP1048', 'karthik.pillai@otsi.co.in', 'Karthik Pillai', 'SAS Programmer', 'Data & Analytics', 'BI & Reporting', 'EMP1008', 'Manoj Kumar K.', '+91 98490 01048', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-02-15'),
    ('EMP1049', 'lakshmi.joshi@otsi.co.in', 'Lakshmi Joshi', 'SAS Programmer', 'Data & Analytics', 'Big Data Engineering', 'EMP1009', 'Naveen Reddy T.', '+91 98490 01049', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-03-24')
ON CONFLICT (employee_id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    designation = EXCLUDED.designation,
    department = EXCLUDED.department,
    team = EXCLUDED.team,
    manager_id = EXCLUDED.manager_id,
    manager_name = EXCLUDED.manager_name,
    role = EXCLUDED.role,
    password_hash = EXCLUDED.password_hash;

INSERT INTO employees (employee_id, email, full_name, designation, department, team, manager_id, manager_name, phone, role, status, password_hash, date_of_joining) VALUES
    ('EMP1050', 'madhav.rao@otsi.co.in', 'Madhav Rao', 'SAS Programmer', 'Data & Analytics', 'Cloud Data Platforms', 'EMP1010', 'Deepak Sharma', '+91 98490 01050', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-04-30'),
    ('EMP1051', 'nandini.patel@otsi.co.in', 'Nandini Patel', 'SAS Administrator', 'Data & Analytics', 'AI & Machine Learning', 'EMP1011', 'Kavitha Swaminathan', '+91 98490 01051', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-06-06'),
    ('EMP1052', 'omkar.nair@otsi.co.in', 'Omkar Nair', 'SAS Administrator', 'Data & Analytics', 'BI & Reporting', 'EMP1008', 'Manoj Kumar K.', '+91 98490 01052', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-07-13'),
    ('EMP1053', 'pooja.kulkarni@otsi.co.in', 'Pooja Kulkarni', 'SAS Administrator', 'Data & Analytics', 'Big Data Engineering', 'EMP1009', 'Naveen Reddy T.', '+91 98490 01053', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-08-19'),
    ('EMP1054', 'rajiv.pillai@otsi.co.in', 'Rajiv Pillai', 'Lead Database Developer', 'Data & Analytics', 'Cloud Data Platforms', 'EMP1010', 'Deepak Sharma', '+91 98490 01054', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-09-25'),
    ('EMP1055', 'sneha.joshi@otsi.co.in', 'Sneha Joshi', 'Lead Database Developer', 'Data & Analytics', 'AI & Machine Learning', 'EMP1011', 'Kavitha Swaminathan', '+91 98490 01055', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-11-01'),
    ('EMP1056', 'tarun.rao@otsi.co.in', 'Tarun Rao', 'Lead Database Developer', 'Data & Analytics', 'BI & Reporting', 'EMP1008', 'Manoj Kumar K.', '+91 98490 01056', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-12-08'),
    ('EMP1057', 'usha.patel@otsi.co.in', 'Usha Patel', 'Lead Database Developer', 'Data & Analytics', 'Big Data Engineering', 'EMP1009', 'Naveen Reddy T.', '+91 98490 01057', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-01-14'),
    ('EMP1058', 'varun.nair@otsi.co.in', 'Varun Nair', 'Lead Database Developer', 'Data & Analytics', 'Cloud Data Platforms', 'EMP1010', 'Deepak Sharma', '+91 98490 01058', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-02-20'),
    ('EMP1059', 'yash.kulkarni@otsi.co.in', 'Yash Kulkarni', 'Database Administrator', 'Data & Analytics', 'AI & Machine Learning', 'EMP1011', 'Kavitha Swaminathan', '+91 98490 01059', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-03-29'),
    ('EMP1060', 'arun.pillai@otsi.co.in', 'Arun Pillai', 'Database Administrator', 'Data & Analytics', 'BI & Reporting', 'EMP1008', 'Manoj Kumar K.', '+91 98490 01060', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-05-05'),
    ('EMP1061', 'bhavana.joshi@otsi.co.in', 'Bhavana Joshi', 'Database Administrator', 'Data & Analytics', 'Big Data Engineering', 'EMP1009', 'Naveen Reddy T.', '+91 98490 01061', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-06-11'),
    ('EMP1062', 'chetan.rao@otsi.co.in', 'Chetan Rao', 'Database Administrator', 'Data & Analytics', 'Cloud Data Platforms', 'EMP1010', 'Deepak Sharma', '+91 98490 01062', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-07-18'),
    ('EMP1063', 'divya.patel@otsi.co.in', 'Divya Patel', 'Big Data Engineer', 'Data & Analytics', 'AI & Machine Learning', 'EMP1011', 'Kavitha Swaminathan', '+91 98490 01063', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-08-24'),
    ('EMP1064', 'ganesh.nair@otsi.co.in', 'Ganesh Nair', 'Big Data Engineer', 'Data & Analytics', 'BI & Reporting', 'EMP1008', 'Manoj Kumar K.', '+91 98490 01064', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-09-30'),
    ('EMP1065', 'harish.kulkarni@otsi.co.in', 'Harish Kulkarni', 'Big Data Engineer', 'Data & Analytics', 'Big Data Engineering', 'EMP1009', 'Naveen Reddy T.', '+91 98490 01065', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-11-06'),
    ('EMP1066', 'ishita.pillai@otsi.co.in', 'Ishita Pillai', 'Big Data Engineer', 'Data & Analytics', 'Cloud Data Platforms', 'EMP1010', 'Deepak Sharma', '+91 98490 01066', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-12-13'),
    ('EMP1067', 'ramesh.chandra@otsi.co.in', 'Ramesh Chandra', 'Technical Manager', 'Application Engineering', 'Full Stack Web & Python', 'EMP1015', 'Venkat Ramana M.', '+91 98490 01067', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2019-11-20'),
    ('EMP1068', 'gita.vani.k.@otsi.co.in', 'Gita Vani K.', 'Project Manager', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1015', 'Venkat Ramana M.', '+91 98490 01068', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2019-11-20'),
    ('EMP1069', 'srikanth.murthy@otsi.co.in', 'Srikanth Murthy', 'Technical Manager', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1015', 'Venkat Ramana M.', '+91 98490 01069', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2019-11-20'),
    ('EMP1070', 'sudhakar.g.@otsi.co.in', 'Sudhakar G.', 'Project Manager', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1015', 'Venkat Ramana M.', '+91 98490 01070', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2019-11-20'),
    ('EMP1071', 'satish.babu@otsi.co.in', 'Satish Babu', 'Technical Lead', 'Application Engineering', 'Full Stack Web & Python', 'EMP1067', 'Ramesh Chandra', '+91 98490 01071', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-02-15'),
    ('EMP1072', 'anusha.p.@otsi.co.in', 'Anusha P.', 'Team Lead', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1068', 'Gita Vani K.', '+91 98490 01072', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-02-15'),
    ('EMP1073', 'mahesh.goud@otsi.co.in', 'Mahesh Goud', 'Technical Lead', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1069', 'Srikanth Murthy', '+91 98490 01073', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-02-15'),
    ('EMP1074', 'rohit.malhotra@otsi.co.in', 'Rohit Malhotra', 'Associate Architect', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1070', 'Sudhakar G.', '+91 98490 01074', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-02-15'),
    ('EMP1075', 'ravi.mallem@otsi.co.in', 'Ravi Mallem', 'Senior Software Engineer', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 58310', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-06-15'),
    ('EMP1076', 'sandhya.chowdary@otsi.co.in', 'Sandhya Chowdary', 'Principal Engineer', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 01076', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-06-22'),
    ('EMP1077', 'tejas.verma@otsi.co.in', 'Tejas Verma', 'Principal Engineer', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1072', 'Anusha P.', '+91 98490 01077', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-08-04'),
    ('EMP1078', 'venkat.banerjee@otsi.co.in', 'Venkat Banerjee', 'Senior Software Engineer', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1073', 'Mahesh Goud', '+91 98490 01078', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-09-16'),
    ('EMP1079', 'zoya.vemula@otsi.co.in', 'Zoya Vemula', 'Senior Software Engineer', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1074', 'Rohit Malhotra', '+91 98490 01079', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-10-29'),
    ('EMP1080', 'ajay.agarwal@otsi.co.in', 'Ajay Agarwal', 'Senior Software Engineer', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 01080', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-12-11'),
    ('EMP1081', 'bhargav.chatterjee@otsi.co.in', 'Bhargav Chatterjee', 'Senior Software Engineer', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1072', 'Anusha P.', '+91 98490 01081', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-01-23'),
    ('EMP1082', 'chaitanya.goud@otsi.co.in', 'Chaitanya Goud', 'Senior Software Engineer', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1073', 'Mahesh Goud', '+91 98490 01082', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-03-07'),
    ('EMP1083', 'deepa.saxena@otsi.co.in', 'Deepa Saxena', 'Senior Software Engineer', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1074', 'Rohit Malhotra', '+91 98490 01083', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-04-19'),
    ('EMP1084', 'eswar.mukherjee@otsi.co.in', 'Eswar Mukherjee', 'Senior Software Engineer', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 01084', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-06-01'),
    ('EMP1085', 'farhan.bandari@otsi.co.in', 'Farhan Bandari', 'Software Engineer', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1072', 'Anusha P.', '+91 98490 01085', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-07-14'),
    ('EMP1086', 'gayatri.tripathi@otsi.co.in', 'Gayatri Tripathi', 'Software Engineer', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1073', 'Mahesh Goud', '+91 98490 01086', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-08-26'),
    ('EMP1087', 'hemant.nambiar@otsi.co.in', 'Hemant Nambiar', 'Software Engineer', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1074', 'Rohit Malhotra', '+91 98490 01087', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-10-08'),
    ('EMP1088', 'indira.koppula@otsi.co.in', 'Indira Koppula', 'Software Engineer', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 01088', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-11-20'),
    ('EMP1089', 'jitendra.singhania@otsi.co.in', 'Jitendra Singhania', 'Software Engineer', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1072', 'Anusha P.', '+91 98490 01089', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-01-28'),
    ('EMP1090', 'kiran.pillai@otsi.co.in', 'Kiran Pillai', 'Software Engineer', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1073', 'Mahesh Goud', '+91 98490 01090', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-03-12'),
    ('EMP1091', 'lalitha.soni@otsi.co.in', 'Lalitha Soni', 'Software Engineer', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1074', 'Rohit Malhotra', '+91 98490 01091', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-04-24'),
    ('EMP1092', 'mohan.chowdary@otsi.co.in', 'Mohan Chowdary', 'Software Engineer', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 01092', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-06-06'),
    ('EMP1093', 'neeraj.verma@otsi.co.in', 'Neeraj Verma', 'Software Engineer', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1072', 'Anusha P.', '+91 98490 01093', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-07-19'),
    ('EMP1094', 'praveen.banerjee@otsi.co.in', 'Praveen Banerjee', 'Associate Software Engineer', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1073', 'Mahesh Goud', '+91 98490 01094', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-08-31'),
    ('EMP1095', 'rakesh.vemula@otsi.co.in', 'Rakesh Vemula', 'Associate Software Engineer', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1074', 'Rohit Malhotra', '+91 98490 01095', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-10-13'),
    ('EMP1096', 'sandhya.agarwal@otsi.co.in', 'Sandhya Agarwal', 'Associate Software Engineer', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 01096', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-11-25'),
    ('EMP1097', 'tejas.chatterjee@otsi.co.in', 'Tejas Chatterjee', 'Associate Software Engineer', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1072', 'Anusha P.', '+91 98490 01097', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-01-07'),
    ('EMP1098', 'venkat.goud@otsi.co.in', 'Venkat Goud', 'Associate Software Engineer', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1073', 'Mahesh Goud', '+91 98490 01098', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-02-19'),
    ('EMP1099', 'zoya.saxena@otsi.co.in', 'Zoya Saxena', 'Associate Software Engineer', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1074', 'Rohit Malhotra', '+91 98490 01099', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-04-03')
ON CONFLICT (employee_id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    designation = EXCLUDED.designation,
    department = EXCLUDED.department,
    team = EXCLUDED.team,
    manager_id = EXCLUDED.manager_id,
    manager_name = EXCLUDED.manager_name,
    role = EXCLUDED.role,
    password_hash = EXCLUDED.password_hash;

INSERT INTO employees (employee_id, email, full_name, designation, department, team, manager_id, manager_name, phone, role, status, password_hash, date_of_joining) VALUES
    ('EMP1100', 'ajay.mukherjee@otsi.co.in', 'Ajay Mukherjee', 'Associate Software Engineer', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 01100', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-05-16'),
    ('EMP1101', 'bhargav.bandari@otsi.co.in', 'Bhargav Bandari', 'Graduate Engineer / Trainee', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1072', 'Anusha P.', '+91 98490 01101', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-06-28'),
    ('EMP1102', 'chaitanya.tripathi@otsi.co.in', 'Chaitanya Tripathi', 'Graduate Engineer / Trainee', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1073', 'Mahesh Goud', '+91 98490 01102', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-08-10'),
    ('EMP1103', 'deepa.nambiar@otsi.co.in', 'Deepa Nambiar', 'Graduate Engineer / Trainee', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1074', 'Rohit Malhotra', '+91 98490 01103', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-09-22'),
    ('EMP1104', 'eswar.koppula@otsi.co.in', 'Eswar Koppula', 'Graduate Engineer / Trainee', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 01104', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-11-04'),
    ('EMP1105', 'farhan.singhania@otsi.co.in', 'Farhan Singhania', 'Graduate Engineer / Trainee', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1072', 'Anusha P.', '+91 98490 01105', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-12-17'),
    ('EMP1106', 'gayatri.pillai@otsi.co.in', 'Gayatri Pillai', 'Senior Front End Developer', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1073', 'Mahesh Goud', '+91 98490 01106', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-01-29'),
    ('EMP1107', 'hemant.soni@otsi.co.in', 'Hemant Soni', 'Senior Front End Developer', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1074', 'Rohit Malhotra', '+91 98490 01107', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-03-13'),
    ('EMP1108', 'indira.chowdary@otsi.co.in', 'Indira Chowdary', 'Senior Front End Developer', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 01108', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-04-25'),
    ('EMP1109', 'jitendra.verma@otsi.co.in', 'Jitendra Verma', 'Senior Front End Developer', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1072', 'Anusha P.', '+91 98490 01109', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-06-07'),
    ('EMP1110', 'kiran.banerjee@otsi.co.in', 'Kiran Banerjee', 'Front End Developer', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1073', 'Mahesh Goud', '+91 98490 01110', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-07-20'),
    ('EMP1111', 'lalitha.vemula@otsi.co.in', 'Lalitha Vemula', 'Front End Developer', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1074', 'Rohit Malhotra', '+91 98490 01111', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-09-01'),
    ('EMP1112', 'mohan.agarwal@otsi.co.in', 'Mohan Agarwal', 'Front End Developer', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 01112', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-10-14'),
    ('EMP1113', 'neeraj.chatterjee@otsi.co.in', 'Neeraj Chatterjee', 'Front End Developer', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1072', 'Anusha P.', '+91 98490 01113', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-11-26'),
    ('EMP1114', 'praveen.goud@otsi.co.in', 'Praveen Goud', 'Web Developer (Python)', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1073', 'Mahesh Goud', '+91 98490 01114', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-01-08'),
    ('EMP1115', 'rakesh.saxena@otsi.co.in', 'Rakesh Saxena', 'Web Developer (Python)', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1074', 'Rohit Malhotra', '+91 98490 01115', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-02-20'),
    ('EMP1116', 'sandhya.mukherjee@otsi.co.in', 'Sandhya Mukherjee', 'Web Developer (Python)', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 01116', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-04-03'),
    ('EMP1117', 'tejas.bandari@otsi.co.in', 'Tejas Bandari', 'Senior Mobile App Developer', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1072', 'Anusha P.', '+91 98490 01117', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-05-16'),
    ('EMP1118', 'venkat.tripathi@otsi.co.in', 'Venkat Tripathi', 'Senior Mobile App Developer', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1073', 'Mahesh Goud', '+91 98490 01118', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-06-28'),
    ('EMP1119', 'zoya.nambiar@otsi.co.in', 'Zoya Nambiar', 'Senior Mobile App Developer', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1074', 'Rohit Malhotra', '+91 98490 01119', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-08-10'),
    ('EMP1120', 'ajay.koppula@otsi.co.in', 'Ajay Koppula', 'Senior Polarion Developer', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 01120', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-09-22'),
    ('EMP1121', 'bhargav.singhania@otsi.co.in', 'Bhargav Singhania', 'Senior Polarion Developer', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1072', 'Anusha P.', '+91 98490 01121', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-11-04'),
    ('EMP1122', 'chaitanya.pillai@otsi.co.in', 'Chaitanya Pillai', 'Senior Polarion Developer', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1073', 'Mahesh Goud', '+91 98490 01122', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-12-17'),
    ('EMP1123', 'deepa.soni@otsi.co.in', 'Deepa Soni', 'VxWorks Engineer', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1074', 'Rohit Malhotra', '+91 98490 01123', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-01-29'),
    ('EMP1124', 'eswar.chowdary@otsi.co.in', 'Eswar Chowdary', 'VxWorks Engineer', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 01124', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-03-13'),
    ('EMP1125', 'farhan.verma@otsi.co.in', 'Farhan Verma', 'Embedded Linux Engineer', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1072', 'Anusha P.', '+91 98490 01125', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-04-25'),
    ('EMP1126', 'gayatri.banerjee@otsi.co.in', 'Gayatri Banerjee', 'Embedded Linux Engineer', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1073', 'Mahesh Goud', '+91 98490 01126', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-06-07'),
    ('EMP1127', 'hemant.vemula@otsi.co.in', 'Hemant Vemula', 'Senior System Engineer', 'Application Engineering', 'ALM & Polarion Practice', 'EMP1074', 'Rohit Malhotra', '+91 98490 01127', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-07-20'),
    ('EMP1128', 'indira.agarwal@otsi.co.in', 'Indira Agarwal', 'Senior System Engineer', 'Application Engineering', 'Full Stack Web & Python', 'EMP1071', 'Satish Babu', '+91 98490 01128', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-09-01'),
    ('EMP1129', 'jitendra.chatterjee@otsi.co.in', 'Jitendra Chatterjee', 'System Engineer', 'Application Engineering', 'Frontend & Mobile Apps', 'EMP1072', 'Anusha P.', '+91 98490 01129', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-10-14'),
    ('EMP1130', 'kiran.goud@otsi.co.in', 'Kiran Goud', 'System Engineer', 'Application Engineering', 'Embedded & IoT Solutions', 'EMP1073', 'Mahesh Goud', '+91 98490 01130', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-11-26'),
    ('EMP1131', 'sanjay.kulkarni@otsi.co.in', 'Sanjay Kulkarni', 'Test Manager', 'Quality Assurance & Testing', 'Functional & Regression QA', 'EMP1012', 'Raghavendra Prasad', '+91 98490 01131', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-05-10'),
    ('EMP1132', 'meenakshi.sundaram@otsi.co.in', 'Meenakshi Sundaram', 'Senior Test Architect', 'Quality Assurance & Testing', 'Automation & Performance QA', 'EMP1012', 'Raghavendra Prasad', '+91 98490 01132', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-05-10'),
    ('EMP1133', 'bipin.bihari@otsi.co.in', 'Bipin Bihari', 'Test Lead', 'Quality Assurance & Testing', 'Mobile & Web QA', 'EMP1012', 'Raghavendra Prasad', '+91 98490 01133', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-05-10'),
    ('EMP1134', 'radhika.nair@otsi.co.in', 'Radhika Nair', 'Senior Test Lead', 'Quality Assurance & Testing', 'Enterprise Systems QA', 'EMP1012', 'Raghavendra Prasad', '+91 98490 01134', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-05-10'),
    ('EMP1135', 'mansi.chauhan@otsi.co.in', 'Mansi Chauhan', 'Senior Test Engineer', 'Quality Assurance & Testing', 'Enterprise Systems QA', 'EMP1134', 'Radhika Nair', '+91 98490 01135', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-11-06'),
    ('EMP1136', 'nikhil.bahl@otsi.co.in', 'Nikhil Bahl', 'Senior Test Engineer', 'Quality Assurance & Testing', 'Functional & Regression QA', 'EMP1131', 'Sanjay Kulkarni', '+91 98490 01136', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-12-05'),
    ('EMP1137', 'pallavi.somani@otsi.co.in', 'Pallavi Somani', 'Senior Test Engineer', 'Quality Assurance & Testing', 'Automation & Performance QA', 'EMP1132', 'Meenakshi Sundaram', '+91 98490 01137', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-01-03'),
    ('EMP1138', 'rohan.sood@otsi.co.in', 'Rohan Sood', 'Senior Test Engineer', 'Quality Assurance & Testing', 'Mobile & Web QA', 'EMP1133', 'Bipin Bihari', '+91 98490 01138', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-02-01'),
    ('EMP1139', 'swati.madan@otsi.co.in', 'Swati Madan', 'Senior Test Engineer', 'Quality Assurance & Testing', 'Enterprise Systems QA', 'EMP1134', 'Radhika Nair', '+91 98490 01139', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-03-02'),
    ('EMP1140', 'amit.pandey@otsi.co.in', 'Amit Pandey', 'Senior Test Engineer', 'Quality Assurance & Testing', 'Functional & Regression QA', 'EMP1131', 'Sanjay Kulkarni', '+91 98490 01140', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-03-31'),
    ('EMP1141', 'bindu.sethi@otsi.co.in', 'Bindu Sethi', 'Test Engineer', 'Quality Assurance & Testing', 'Automation & Performance QA', 'EMP1132', 'Meenakshi Sundaram', '+91 98490 01141', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-04-29'),
    ('EMP1142', 'charan.bhatnagar@otsi.co.in', 'Charan Bhatnagar', 'Test Engineer', 'Quality Assurance & Testing', 'Mobile & Web QA', 'EMP1133', 'Bipin Bihari', '+91 98490 01142', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-05-28'),
    ('EMP1143', 'deepak.arora@otsi.co.in', 'Deepak Arora', 'Test Engineer', 'Quality Assurance & Testing', 'Enterprise Systems QA', 'EMP1134', 'Radhika Nair', '+91 98490 01143', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-06-26'),
    ('EMP1144', 'esha.goyal@otsi.co.in', 'Esha Goyal', 'Test Engineer', 'Quality Assurance & Testing', 'Functional & Regression QA', 'EMP1131', 'Sanjay Kulkarni', '+91 98490 01144', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-07-25'),
    ('EMP1145', 'girish.kapoor@otsi.co.in', 'Girish Kapoor', 'Test Engineer', 'Quality Assurance & Testing', 'Automation & Performance QA', 'EMP1132', 'Meenakshi Sundaram', '+91 98490 01145', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-08-23'),
    ('EMP1146', 'haritha.khatri@otsi.co.in', 'Haritha Khatri', 'Test Engineer', 'Quality Assurance & Testing', 'Mobile & Web QA', 'EMP1133', 'Bipin Bihari', '+91 98490 01146', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-09-21'),
    ('EMP1147', 'jagadish.chauhan@otsi.co.in', 'Jagadish Chauhan', 'Test Engineer', 'Quality Assurance & Testing', 'Enterprise Systems QA', 'EMP1134', 'Radhika Nair', '+91 98490 01147', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-10-20'),
    ('EMP1148', 'komal.bahl@otsi.co.in', 'Komal Bahl', 'Test Engineer', 'Quality Assurance & Testing', 'Functional & Regression QA', 'EMP1131', 'Sanjay Kulkarni', '+91 98490 01148', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-11-18'),
    ('EMP1149', 'lokesh.somani@otsi.co.in', 'Lokesh Somani', 'Associate Test Engineer', 'Quality Assurance & Testing', 'Automation & Performance QA', 'EMP1132', 'Meenakshi Sundaram', '+91 98490 01149', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-12-17')
ON CONFLICT (employee_id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    designation = EXCLUDED.designation,
    department = EXCLUDED.department,
    team = EXCLUDED.team,
    manager_id = EXCLUDED.manager_id,
    manager_name = EXCLUDED.manager_name,
    role = EXCLUDED.role,
    password_hash = EXCLUDED.password_hash;

INSERT INTO employees (employee_id, email, full_name, designation, department, team, manager_id, manager_name, phone, role, status, password_hash, date_of_joining) VALUES
    ('EMP1150', 'mansi.sood@otsi.co.in', 'Mansi Sood', 'Associate Test Engineer', 'Quality Assurance & Testing', 'Mobile & Web QA', 'EMP1133', 'Bipin Bihari', '+91 98490 01150', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-01-15'),
    ('EMP1151', 'nikhil.madan@otsi.co.in', 'Nikhil Madan', 'Associate Test Engineer', 'Quality Assurance & Testing', 'Enterprise Systems QA', 'EMP1134', 'Radhika Nair', '+91 98490 01151', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-02-13'),
    ('EMP1152', 'pallavi.pandey@otsi.co.in', 'Pallavi Pandey', 'Associate Test Engineer', 'Quality Assurance & Testing', 'Functional & Regression QA', 'EMP1131', 'Sanjay Kulkarni', '+91 98490 01152', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-03-13'),
    ('EMP1153', 'rohan.sethi@otsi.co.in', 'Rohan Sethi', 'Associate Test Engineer', 'Quality Assurance & Testing', 'Automation & Performance QA', 'EMP1132', 'Meenakshi Sundaram', '+91 98490 01153', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-04-11'),
    ('EMP1154', 'swati.bhatnagar@otsi.co.in', 'Swati Bhatnagar', 'Associate Test Engineer', 'Quality Assurance & Testing', 'Mobile & Web QA', 'EMP1133', 'Bipin Bihari', '+91 98490 01154', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-05-10'),
    ('EMP1155', 'amit.arora@otsi.co.in', 'Amit Arora', 'QA Engineer', 'Quality Assurance & Testing', 'Enterprise Systems QA', 'EMP1134', 'Radhika Nair', '+91 98490 01155', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-06-08'),
    ('EMP1156', 'bindu.goyal@otsi.co.in', 'Bindu Goyal', 'QA Engineer', 'Quality Assurance & Testing', 'Functional & Regression QA', 'EMP1131', 'Sanjay Kulkarni', '+91 98490 01156', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-07-07'),
    ('EMP1157', 'charan.kapoor@otsi.co.in', 'Charan Kapoor', 'QA Engineer', 'Quality Assurance & Testing', 'Automation & Performance QA', 'EMP1132', 'Meenakshi Sundaram', '+91 98490 01157', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-08-05'),
    ('EMP1158', 'deepak.khatri@otsi.co.in', 'Deepak Khatri', 'QA Engineer', 'Quality Assurance & Testing', 'Mobile & Web QA', 'EMP1133', 'Bipin Bihari', '+91 98490 01158', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-09-03'),
    ('EMP1159', 'esha.chauhan@otsi.co.in', 'Esha Chauhan', 'QA Engineer', 'Quality Assurance & Testing', 'Enterprise Systems QA', 'EMP1134', 'Radhika Nair', '+91 98490 01159', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-10-02'),
    ('EMP1160', 'girish.bahl@otsi.co.in', 'Girish Bahl', 'Performance & Load Testing Specialist', 'Quality Assurance & Testing', 'Functional & Regression QA', 'EMP1131', 'Sanjay Kulkarni', '+91 98490 01160', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-10-31'),
    ('EMP1161', 'haritha.somani@otsi.co.in', 'Haritha Somani', 'Performance & Load Testing Specialist', 'Quality Assurance & Testing', 'Automation & Performance QA', 'EMP1132', 'Meenakshi Sundaram', '+91 98490 01161', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-11-29'),
    ('EMP1162', 'jagadish.sood@otsi.co.in', 'Jagadish Sood', 'Performance & Load Testing Specialist', 'Quality Assurance & Testing', 'Mobile & Web QA', 'EMP1133', 'Bipin Bihari', '+91 98490 01162', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-12-28'),
    ('EMP1163', 'komal.madan@otsi.co.in', 'Komal Madan', 'Performance & Load Testing Specialist', 'Quality Assurance & Testing', 'Enterprise Systems QA', 'EMP1134', 'Radhika Nair', '+91 98490 01163', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-01-26'),
    ('EMP1164', 'lokesh.pandey@otsi.co.in', 'Lokesh Pandey', 'Performance & Load Testing Specialist', 'Quality Assurance & Testing', 'Functional & Regression QA', 'EMP1131', 'Sanjay Kulkarni', '+91 98490 01164', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-02-24'),
    ('EMP1165', 'madhuri.saha@otsi.co.in', 'Madhuri Saha', 'Director, Strategy & Delivery', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01165', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-06-16'),
    ('EMP1166', 'naveen.majumdar@otsi.co.in', 'Naveen Majumdar', 'Principal Architect', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01166', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-07-17'),
    ('EMP1167', 'pratibha.chakraborty@otsi.co.in', 'Pratibha Chakraborty', 'Principal Architect', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01167', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-08-17'),
    ('EMP1168', 'ritesh.dutta@otsi.co.in', 'Ritesh Dutta', 'Architect', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01168', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-09-17'),
    ('EMP1169', 'sunita.banerjee@otsi.co.in', 'Sunita Banerjee', 'Architect', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01169', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-10-18'),
    ('EMP1170', 'abhishek.sengupta@otsi.co.in', 'Abhishek Sengupta', 'Associate Architect', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01170', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-11-18'),
    ('EMP1171', 'bhavik.bhattacharya@otsi.co.in', 'Bhavik Bhattacharya', 'Associate Architect', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01171', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-12-19'),
    ('EMP1172', 'chetna.roy@otsi.co.in', 'Chetna Roy', 'Senior Consultant', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01172', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-01-19'),
    ('EMP1173', 'devendra.goswami@otsi.co.in', 'Devendra Goswami', 'Senior Consultant', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01173', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-02-19'),
    ('EMP1174', 'garima.saha@otsi.co.in', 'Garima Saha', 'Senior Consultant', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01174', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-03-22'),
    ('EMP1175', 'himanshu.majumdar@otsi.co.in', 'Himanshu Majumdar', 'Consultant', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01175', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-04-22'),
    ('EMP1176', 'isha.chakraborty@otsi.co.in', 'Isha Chakraborty', 'Consultant', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01176', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-05-23'),
    ('EMP1177', 'kunal.dutta@otsi.co.in', 'Kunal Dutta', 'Senior Analyst', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01177', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-06-23'),
    ('EMP1178', 'madhuri.banerjee@otsi.co.in', 'Madhuri Banerjee', 'Senior Analyst', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01178', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-07-24'),
    ('EMP1179', 'naveen.sengupta@otsi.co.in', 'Naveen Sengupta', 'Business Analyst', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01179', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-08-24'),
    ('EMP1180', 'pratibha.bhattacharya@otsi.co.in', 'Pratibha Bhattacharya', 'Business Analyst', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01180', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-09-24'),
    ('EMP1181', 'ritesh.roy@otsi.co.in', 'Ritesh Roy', 'Technical Project Manager', 'Digital Transformation', 'Strategy & Cloud Advisory', 'EMP1013', 'Siddharth Mehta', '+91 98490 01181', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-10-25'),
    ('EMP1182', 'venkatesh.babu@otsi.co.in', 'Venkatesh Babu', 'Technical Manager - IT & Cloud', 'IT Infrastructure & Cloud', 'Cloud Infrastructure & Ops', 'EMP1014', 'Sunil Chander', '+91 98490 01182', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2019-12-01'),
    ('EMP1183', 'syed.mustaq@otsi.co.in', 'Syed Mustaq', 'Lead System Network Administrator', 'IT Infrastructure & Cloud', 'Network Security & Telecom', 'EMP1014', 'Sunil Chander', '+91 98490 01183', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2019-12-01'),
    ('EMP1184', 'balu.babu@otsi.co.in', 'Balu Babu', 'Senior System Administrator', 'IT Infrastructure & Cloud', 'Cloud Infrastructure & Ops', 'EMP1182', 'Venkatesh Babu', '+91 98490 01184', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-12-26'),
    ('EMP1185', 'gopi.kumar@otsi.co.in', 'Gopi Kumar', 'Senior System Administrator', 'IT Infrastructure & Cloud', 'Network Security & Telecom', 'EMP1183', 'Syed Mustaq', '+91 98490 01185', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-01-12'),
    ('EMP1186', 'muralidhar.joshi@otsi.co.in', 'Muralidhar Joshi', 'Senior System Administrator', 'IT Infrastructure & Cloud', 'Cloud Infrastructure & Ops', 'EMP1182', 'Venkatesh Babu', '+91 98490 01186', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-01-29'),
    ('EMP1187', 'prashanth.yadav@otsi.co.in', 'Prashanth Yadav', 'System Administrator', 'IT Infrastructure & Cloud', 'Network Security & Telecom', 'EMP1183', 'Syed Mustaq', '+91 98490 01187', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-02-15'),
    ('EMP1188', 'kiran.kulkarni@otsi.co.in', 'Kiran Kulkarni', 'System Administrator', 'IT Infrastructure & Cloud', 'Cloud Infrastructure & Ops', 'EMP1182', 'Venkatesh Babu', '+91 98490 01188', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-03-04'),
    ('EMP1189', 'nagaraj.sharma@otsi.co.in', 'Nagaraj Sharma', 'System Administrator', 'IT Infrastructure & Cloud', 'Network Security & Telecom', 'EMP1183', 'Syed Mustaq', '+91 98490 01189', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-03-21'),
    ('EMP1190', 'raju.singh@otsi.co.in', 'Raju Singh', 'System Administrator', 'IT Infrastructure & Cloud', 'Cloud Infrastructure & Ops', 'EMP1182', 'Venkatesh Babu', '+91 98490 01190', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-04-07'),
    ('EMP1191', 'shiva.reddy@otsi.co.in', 'Shiva Reddy', 'System Network Administrator', 'IT Infrastructure & Cloud', 'Network Security & Telecom', 'EMP1183', 'Syed Mustaq', '+91 98490 01191', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-04-24'),
    ('EMP1192', 'pavan.patel@otsi.co.in', 'Pavan Patel', 'System Network Administrator', 'IT Infrastructure & Cloud', 'Cloud Infrastructure & Ops', 'EMP1182', 'Venkatesh Babu', '+91 98490 01192', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-05-11'),
    ('EMP1193', 'vijay.babu@otsi.co.in', 'Vijay Babu', 'System Network Administrator', 'IT Infrastructure & Cloud', 'Network Security & Telecom', 'EMP1183', 'Syed Mustaq', '+91 98490 01193', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-05-28'),
    ('EMP1194', 'anil.kumar@otsi.co.in', 'Anil Kumar', 'Global Service Desk Agent', 'IT Infrastructure & Cloud', 'Cloud Infrastructure & Ops', 'EMP1182', 'Venkatesh Babu', '+91 98490 01194', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-06-14'),
    ('EMP1195', 'satya.joshi@otsi.co.in', 'Satya Joshi', 'Global Service Desk Agent', 'IT Infrastructure & Cloud', 'Network Security & Telecom', 'EMP1183', 'Syed Mustaq', '+91 98490 01195', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-07-01'),
    ('EMP1196', 'balu.yadav@otsi.co.in', 'Balu Yadav', 'Global Service Desk Agent', 'IT Infrastructure & Cloud', 'Cloud Infrastructure & Ops', 'EMP1182', 'Venkatesh Babu', '+91 98490 01196', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-07-18'),
    ('EMP1197', 'gopi.kulkarni@otsi.co.in', 'Gopi Kulkarni', 'Global Service Desk Agent', 'IT Infrastructure & Cloud', 'Network Security & Telecom', 'EMP1183', 'Syed Mustaq', '+91 98490 01197', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-08-04'),
    ('EMP1198', 'muralidhar.sharma@otsi.co.in', 'Muralidhar Sharma', 'Specialist – IT Support', 'IT Infrastructure & Cloud', 'Cloud Infrastructure & Ops', 'EMP1182', 'Venkatesh Babu', '+91 98490 01198', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-08-21'),
    ('EMP1199', 'prashanth.singh@otsi.co.in', 'Prashanth Singh', 'Specialist – IT Support', 'IT Infrastructure & Cloud', 'Network Security & Telecom', 'EMP1183', 'Syed Mustaq', '+91 98490 01199', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-09-07')
ON CONFLICT (employee_id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    designation = EXCLUDED.designation,
    department = EXCLUDED.department,
    team = EXCLUDED.team,
    manager_id = EXCLUDED.manager_id,
    manager_name = EXCLUDED.manager_name,
    role = EXCLUDED.role,
    password_hash = EXCLUDED.password_hash;

INSERT INTO employees (employee_id, email, full_name, designation, department, team, manager_id, manager_name, phone, role, status, password_hash, date_of_joining) VALUES
    ('EMP1200', 'kiran.reddy@otsi.co.in', 'Kiran Reddy', 'Specialist – IT Support', 'IT Infrastructure & Cloud', 'Cloud Infrastructure & Ops', 'EMP1182', 'Venkatesh Babu', '+91 98490 01200', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-09-24'),
    ('EMP1201', 'nagaraj.patel@otsi.co.in', 'Nagaraj Patel', 'Lab Admin', 'IT Infrastructure & Cloud', 'Network Security & Telecom', 'EMP1183', 'Syed Mustaq', '+91 98490 01201', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-10-11'),
    ('EMP1202', 'raju.babu@otsi.co.in', 'Raju Babu', 'Lab Admin', 'IT Infrastructure & Cloud', 'Cloud Infrastructure & Ops', 'EMP1182', 'Venkatesh Babu', '+91 98490 01202', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-10-28'),
    ('EMP1203', 'meera.talwar@otsi.co.in', 'Meera Talwar', 'Director of Client Success', 'Sales & Business Development', 'Commercial Enterprise Sales', 'EMP1004', 'Vikramaditya Rao', '+91 98490 01203', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-07-06'),
    ('EMP1204', 'neha.oberoi@otsi.co.in', 'Neha Oberoi', 'Director of Client Success', 'Sales & Business Development', 'Public Sector Sales', 'EMP1003', 'Suresh Nambiar', '+91 98490 01204', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-07-29'),
    ('EMP1205', 'rohan.khanna@otsi.co.in', 'Rohan Khanna', 'Senior Manager – Sales and Account Growth', 'Sales & Business Development', 'Commercial Enterprise Sales', 'EMP1004', 'Vikramaditya Rao', '+91 98490 01205', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-08-21'),
    ('EMP1206', 'simran.mehra@otsi.co.in', 'Simran Mehra', 'Senior Manager – Sales and Account Growth', 'Sales & Business Development', 'Public Sector Sales', 'EMP1003', 'Suresh Nambiar', '+91 98490 01206', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-09-13'),
    ('EMP1207', 'tanya.malhotra@otsi.co.in', 'Tanya Malhotra', 'Senior Manager – Sales and Account Growth', 'Sales & Business Development', 'Commercial Enterprise Sales', 'EMP1004', 'Vikramaditya Rao', '+91 98490 01207', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-10-06'),
    ('EMP1208', 'varun.singhal@otsi.co.in', 'Varun Singhal', 'Manager – Alliances & Partnerships', 'Sales & Business Development', 'Public Sector Sales', 'EMP1003', 'Suresh Nambiar', '+91 98490 01208', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-10-29'),
    ('EMP1209', 'zain.chopra@otsi.co.in', 'Zain Chopra', 'Manager – Alliances & Partnerships', 'Sales & Business Development', 'Commercial Enterprise Sales', 'EMP1004', 'Vikramaditya Rao', '+91 98490 01209', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-11-21'),
    ('EMP1210', 'aditya.kapoor@otsi.co.in', 'Aditya Kapoor', 'Manager – Alliances & Partnerships', 'Sales & Business Development', 'Public Sector Sales', 'EMP1003', 'Suresh Nambiar', '+91 98490 01210', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-12-14'),
    ('EMP1211', 'dev.batra@otsi.co.in', 'Dev Batra', 'Account Executive', 'Sales & Business Development', 'Commercial Enterprise Sales', 'EMP1004', 'Vikramaditya Rao', '+91 98490 01211', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-01-06'),
    ('EMP1212', 'gautam.talwar@otsi.co.in', 'Gautam Talwar', 'Account Executive', 'Sales & Business Development', 'Public Sector Sales', 'EMP1003', 'Suresh Nambiar', '+91 98490 01212', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-01-29'),
    ('EMP1213', 'kabir.oberoi@otsi.co.in', 'Kabir Oberoi', 'Account Executive', 'Sales & Business Development', 'Commercial Enterprise Sales', 'EMP1004', 'Vikramaditya Rao', '+91 98490 01213', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-02-21'),
    ('EMP1214', 'meera.khanna@otsi.co.in', 'Meera Khanna', 'Account Executive', 'Sales & Business Development', 'Public Sector Sales', 'EMP1003', 'Suresh Nambiar', '+91 98490 01214', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-03-15'),
    ('EMP1215', 'neha.mehra@otsi.co.in', 'Neha Mehra', 'Account Executive', 'Sales & Business Development', 'Commercial Enterprise Sales', 'EMP1004', 'Vikramaditya Rao', '+91 98490 01215', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-04-07'),
    ('EMP1216', 'rohan.malhotra@otsi.co.in', 'Rohan Malhotra', 'Sales & Business Development Executive', 'Sales & Business Development', 'Public Sector Sales', 'EMP1003', 'Suresh Nambiar', '+91 98490 01216', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-04-30'),
    ('EMP1217', 'simran.singhal@otsi.co.in', 'Simran Singhal', 'Sales & Business Development Executive', 'Sales & Business Development', 'Commercial Enterprise Sales', 'EMP1004', 'Vikramaditya Rao', '+91 98490 01217', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-05-23'),
    ('EMP1218', 'tanya.chopra@otsi.co.in', 'Tanya Chopra', 'Sales & Business Development Executive', 'Sales & Business Development', 'Public Sector Sales', 'EMP1003', 'Suresh Nambiar', '+91 98490 01218', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-06-15'),
    ('EMP1219', 'varun.kapoor@otsi.co.in', 'Varun Kapoor', 'Sales & Business Development Executive', 'Sales & Business Development', 'Commercial Enterprise Sales', 'EMP1004', 'Vikramaditya Rao', '+91 98490 01219', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-07-08'),
    ('EMP1220', 'zain.batra@otsi.co.in', 'Zain Batra', 'Sales & Business Development Executive', 'Sales & Business Development', 'Public Sector Sales', 'EMP1003', 'Suresh Nambiar', '+91 98490 01220', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2024-07-31'),
    ('EMP1221', 'hemalatha.kadam@otsi.co.in', 'Hemalatha Kadam', 'General Manager – PMO & Operations', 'Operations & PMO', 'Resource & Logistics Operations', 'EMP1005', 'Subhashini R.', '+91 98490 01221', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-07-09'),
    ('EMP1222', 'jayashree.patil@otsi.co.in', 'Jayashree Patil', 'Senior Manager – Project Delivery', 'Operations & PMO', 'Resource & Logistics Operations', 'EMP1005', 'Subhashini R.', '+91 98490 01222', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-07-28'),
    ('EMP1223', 'kishore.more@otsi.co.in', 'Kishore More', 'Resource Manager', 'Operations & PMO', 'Resource & Logistics Operations', 'EMP1005', 'Subhashini R.', '+91 98490 01223', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-08-16'),
    ('EMP1224', 'anand.deshpande@otsi.co.in', 'Anand Deshpande', 'Resource Manager', 'Operations & PMO', 'Resource & Logistics Operations', 'EMP1005', 'Subhashini R.', '+91 98490 01224', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-09-04'),
    ('EMP1225', 'bhavna.shinde@otsi.co.in', 'Bhavna Shinde', 'Associate Logistics Analyst', 'Operations & PMO', 'Resource & Logistics Operations', 'EMP1005', 'Subhashini R.', '+91 98490 01225', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-09-23'),
    ('EMP1226', 'chitra.bhosale@otsi.co.in', 'Chitra Bhosale', 'Associate Logistics Analyst', 'Operations & PMO', 'Resource & Logistics Operations', 'EMP1005', 'Subhashini R.', '+91 98490 01226', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-10-12'),
    ('EMP1227', 'dinesh.kulkarni@otsi.co.in', 'Dinesh Kulkarni', 'Senior Executive – Operations', 'Operations & PMO', 'Resource & Logistics Operations', 'EMP1005', 'Subhashini R.', '+91 98490 01227', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-10-31'),
    ('EMP1228', 'geeta.gaikwad@otsi.co.in', 'Geeta Gaikwad', 'Senior Executive – Operations', 'Operations & PMO', 'Resource & Logistics Operations', 'EMP1005', 'Subhashini R.', '+91 98490 01228', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-11-19'),
    ('EMP1229', 'hemalatha.kadam.emp1229@otsi.co.in', 'Hemalatha Kadam', 'Manager – Contracts & Administration', 'Operations & PMO', 'Resource & Logistics Operations', 'EMP1005', 'Subhashini R.', '+91 98490 01229', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-12-08'),
    ('EMP1230', 'jayashree.patil.emp1230@otsi.co.in', 'Jayashree Patil', 'Manager – Contracts & Administration', 'Operations & PMO', 'Resource & Logistics Operations', 'EMP1005', 'Subhashini R.', '+91 98490 01230', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2023-12-27'),
    ('EMP1231', 'kavita.krishnan@otsi.co.in', 'Kavita Krishnan', 'HR Manager', 'Human Resources', 'HR Operations & People Management', 'EMP1006', 'Priyanka Sengupta', '+91 98490 01231', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2019-08-15'),
    ('EMP1232', 'rajeshwari.sharma@otsi.co.in', 'Rajeshwari Sharma', 'HR Asst Manager', 'Human Resources', 'HR Operations & People Management', 'EMP1231', 'Kavita Krishnan', '+91 98490 01232', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-03-10'),
    ('EMP1233', 'ananya.sen@otsi.co.in', 'Ananya Sen', 'Sr. HR Executive', 'Human Resources', 'HR Operations & People Management', 'EMP1232', 'Rajeshwari Sharma', '+91 98490 01233', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-01-15'),
    ('EMP1234', 'pooja.verma@otsi.co.in', 'Pooja Verma', 'HR Executive', 'Human Resources', 'HR Operations & People Management', 'EMP1233', 'Ananya Sen', '+91 98490 01234', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-04-10'),
    ('EMP1235', 'shruti.iyer@otsi.co.in', 'Shruti Iyer', 'HR Specialist', 'Human Resources', 'HR Operations & People Management', 'EMP1231', 'Kavita Krishnan', '+91 98490 01235', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-07-20'),
    ('EMP1236', 'aarti.venkatesh@otsi.co.in', 'Aarti Venkatesh', 'Senior Specialist HRBP', 'Human Resources', 'HR Operations & People Management', 'EMP1231', 'Kavita Krishnan', '+91 98490 01236', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-11-05'),
    ('EMP1237', 'divya.subramanian@otsi.co.in', 'Divya Subramanian', 'HR Business Partner', 'Human Resources', 'HR Operations & People Management', 'EMP1231', 'Kavita Krishnan', '+91 98490 01237', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-02-18'),
    ('EMP1238', 'vikram.malhotra@otsi.co.in', 'Vikram Malhotra', 'Technical Manager', 'Human Resources', 'Talent Acquisition & Technical Recruiting', 'EMP1006', 'Priyanka Sengupta', '+91 98490 01238', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2019-10-01'),
    ('EMP1239', 'lavanya.sundaram@otsi.co.in', 'Lavanya Sundaram', 'Sr. Technical Recruiter', 'Human Resources', 'Talent Acquisition & Technical Recruiting', 'EMP1238', 'Vikram Malhotra', '+91 98490 01239', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-06-15'),
    ('EMP1240', 'karthik.swaminathan@otsi.co.in', 'Karthik Swaminathan', 'Sr. Technical Recruiter', 'Human Resources', 'Talent Acquisition & Technical Recruiting', 'EMP1238', 'Vikram Malhotra', '+91 98490 01240', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-08-20'),
    ('EMP1241', 'nandita.chandran@otsi.co.in', 'Nandita Chandran', 'Technical Recruiter', 'Human Resources', 'Talent Acquisition & Technical Recruiting', 'EMP1238', 'Vikram Malhotra', '+91 98490 01241', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-03-12'),
    ('EMP1242', 'rahul.bose@otsi.co.in', 'Rahul Bose', 'Technical Recruiter', 'Human Resources', 'Talent Acquisition & Technical Recruiting', 'EMP1238', 'Vikram Malhotra', '+91 98490 01242', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-05-19'),
    ('EMP1243', 'sneha.reddy@otsi.co.in', 'Sneha Reddy', 'Associate Recruiter', 'Human Resources', 'Talent Acquisition & Technical Recruiting', 'EMP1239', 'Lavanya Sundaram', '+91 98490 01243', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-08-01'),
    ('EMP1244', 'amitabh.das@otsi.co.in', 'Amitabh Das', 'Associate Recruiter', 'Human Resources', 'Talent Acquisition & Technical Recruiting', 'EMP1240', 'Karthik Swaminathan', '+91 98490 01244', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2022-10-15'),
    ('EMP1245', 'rameshwar.patil@otsi.co.in', 'Rameshwar Patil', 'Resource Manager', 'Human Resources', 'Resource Management & Staffing', 'EMP1006', 'Priyanka Sengupta', '+91 98490 01245', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2020-04-01'),
    ('EMP1246', 'bhavna.shinde.emp1246@otsi.co.in', 'Bhavna Shinde', 'Associate Resource Manager', 'Human Resources', 'Resource Management & Staffing', 'EMP1245', 'Rameshwar Patil', '+91 98490 01246', 'hr', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-09-10'),
    ('EMP1247', 'prashant.maheshwari@otsi.co.in', 'Prashant Maheshwari', 'Senior Accountant', 'Finance, Compliance & Administration', 'Finance & Statutory Compliance', 'EMP1005', 'Subhashini R.', '+91 98490 01247', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-11-07'),
    ('EMP1248', 'ramesh.garg@otsi.co.in', 'Ramesh Garg', 'Accountant', 'Finance, Compliance & Administration', 'Finance & Statutory Compliance', 'EMP1005', 'Subhashini R.', '+91 98490 01248', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-11-30'),
    ('EMP1249', 'sridhar.bansal@otsi.co.in', 'Sridhar Bansal', 'Senior Billing Analyst', 'Finance, Compliance & Administration', 'Finance & Statutory Compliance', 'EMP1005', 'Subhashini R.', '+91 98490 01249', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2025-12-23')
ON CONFLICT (employee_id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    designation = EXCLUDED.designation,
    department = EXCLUDED.department,
    team = EXCLUDED.team,
    manager_id = EXCLUDED.manager_id,
    manager_name = EXCLUDED.manager_name,
    role = EXCLUDED.role,
    password_hash = EXCLUDED.password_hash;

INSERT INTO employees (employee_id, email, full_name, designation, department, team, manager_id, manager_name, phone, role, status, password_hash, date_of_joining) VALUES
    ('EMP1250', 'alok.singhal@otsi.co.in', 'Alok Singhal', 'Analyst – Cash Application', 'Finance, Compliance & Administration', 'Finance & Statutory Compliance', 'EMP1005', 'Subhashini R.', '+91 98490 01250', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2026-01-15'),
    ('EMP1251', 'bhaskar.khandelwal@otsi.co.in', 'Bhaskar Khandelwal', 'Senior Compliance Analyst', 'Finance, Compliance & Administration', 'Finance & Statutory Compliance', 'EMP1005', 'Subhashini R.', '+91 98490 01251', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2026-02-07'),
    ('EMP1252', 'gopal.jain@otsi.co.in', 'Gopal Jain', 'Senior KYC Specialist', 'Finance, Compliance & Administration', 'Finance & Statutory Compliance', 'EMP1005', 'Subhashini R.', '+91 98490 01252', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2026-03-02'),
    ('EMP1253', 'harish.goel@otsi.co.in', 'Harish Goel', 'Executive Assistant', 'Finance, Compliance & Administration', 'Finance & Statutory Compliance', 'EMP1005', 'Subhashini R.', '+91 98490 01253', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-04-20'),
    ('EMP1254', 'keshav.agrawal@otsi.co.in', 'Keshav Agrawal', 'Admin Executive', 'Finance, Compliance & Administration', 'Finance & Statutory Compliance', 'EMP1005', 'Subhashini R.', '+91 98490 01254', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-05-13'),
    ('EMP1255', 'manish.mittal@otsi.co.in', 'Manish Mittal', 'Facility Assistant', 'Finance, Compliance & Administration', 'Finance & Statutory Compliance', 'EMP1005', 'Subhashini R.', '+91 98490 01255', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-06-05'),
    ('EMP1256', 'nitin.maheshwari@otsi.co.in', 'Nitin Maheshwari', 'Graphic Designer', 'Finance, Compliance & Administration', 'Finance & Statutory Compliance', 'EMP1005', 'Subhashini R.', '+91 98490 01256', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de', '2021-06-28')
ON CONFLICT (employee_id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    designation = EXCLUDED.designation,
    department = EXCLUDED.department,
    team = EXCLUDED.team,
    manager_id = EXCLUDED.manager_id,
    manager_name = EXCLUDED.manager_name,
    role = EXCLUDED.role,
    password_hash = EXCLUDED.password_hash;

-- ─────────────────────────────────────────────────────────
-- 5. SEED LEAVE BALANCES FOR ALL EMPLOYEES
-- ─────────────────────────────────────────────────────────
INSERT INTO leave_balance (employee_id, casual_leave, sick_leave, earned_leave, bereavement_leave, marriage_leave, lop_leave) VALUES
    ('OTSI0001', 12, 8, 20.0, 3, 0, 0),
    ('EMP1001', 12, 8, 20.0, 3, 0, 0),
    ('EMP1000', 12, 8, 20.0, 3, 0, 0),
    ('EMP1003', 12, 8, 20.0, 3, 0, 0),
    ('EMP1004', 12, 8, 20.0, 3, 0, 0),
    ('EMP1005', 12, 8, 20.0, 3, 0, 0),
    ('EMP1006', 12, 8, 20.0, 3, 0, 0),
    ('EMP1007', 12, 8, 20.0, 3, 0, 0),
    ('EMP1008', 12, 8, 20.0, 3, 0, 0),
    ('EMP1009', 12, 8, 20.0, 3, 0, 0),
    ('EMP1010', 12, 8, 20.0, 3, 0, 0),
    ('EMP1011', 12, 8, 20.0, 3, 0, 0),
    ('EMP1012', 12, 8, 20.0, 3, 0, 0),
    ('EMP1013', 12, 8, 20.0, 3, 0, 0),
    ('EMP1014', 12, 8, 20.0, 3, 0, 0),
    ('EMP1015', 12, 8, 20.0, 3, 0, 0),
    ('EMP1016', 12, 8, 20.0, 3, 0, 0),
    ('EMP1017', 12, 8, 20.0, 3, 0, 0),
    ('EMP1018', 12, 8, 20.0, 3, 0, 0),
    ('EMP1019', 12, 8, 20.0, 3, 0, 0),
    ('EMP1020', 12, 8, 20.0, 3, 0, 0),
    ('EMP1021', 12, 8, 20.0, 3, 0, 0),
    ('EMP1022', 12, 8, 20.0, 3, 0, 0),
    ('EMP1023', 12, 8, 20.0, 3, 0, 0),
    ('EMP1024', 12, 8, 20.0, 3, 0, 0),
    ('EMP1025', 12, 8, 20.0, 3, 0, 0),
    ('EMP1026', 12, 8, 20.0, 3, 0, 0),
    ('EMP1027', 12, 8, 20.0, 3, 0, 0),
    ('EMP1028', 12, 8, 20.0, 3, 0, 0),
    ('EMP1029', 12, 8, 20.0, 3, 0, 0),
    ('EMP1030', 12, 8, 20.0, 3, 0, 0),
    ('EMP1031', 12, 8, 20.0, 3, 0, 0),
    ('EMP1032', 12, 8, 20.0, 3, 0, 0),
    ('EMP1033', 12, 8, 20.0, 3, 0, 0),
    ('EMP1034', 12, 8, 20.0, 3, 0, 0),
    ('EMP1035', 12, 8, 20.0, 3, 0, 0),
    ('EMP1036', 12, 8, 20.0, 3, 0, 0),
    ('EMP1037', 12, 8, 20.0, 3, 0, 0),
    ('EMP1038', 12, 8, 20.0, 3, 0, 0),
    ('EMP1039', 12, 8, 20.0, 3, 0, 0),
    ('EMP1040', 12, 8, 20.0, 3, 0, 0),
    ('EMP1041', 12, 8, 20.0, 3, 0, 0),
    ('EMP1042', 12, 8, 20.0, 3, 0, 0),
    ('EMP1043', 12, 8, 20.0, 3, 0, 0),
    ('EMP1044', 12, 8, 20.0, 3, 0, 0),
    ('EMP1045', 12, 8, 20.0, 3, 0, 0),
    ('EMP1046', 12, 8, 20.0, 3, 0, 0),
    ('EMP1047', 12, 8, 20.0, 3, 0, 0),
    ('EMP1048', 12, 8, 20.0, 3, 0, 0),
    ('EMP1049', 12, 8, 20.0, 3, 0, 0)
ON CONFLICT (employee_id) DO NOTHING;

INSERT INTO leave_balance (employee_id, casual_leave, sick_leave, earned_leave, bereavement_leave, marriage_leave, lop_leave) VALUES
    ('EMP1050', 12, 8, 20.0, 3, 0, 0),
    ('EMP1051', 12, 8, 20.0, 3, 0, 0),
    ('EMP1052', 12, 8, 20.0, 3, 0, 0),
    ('EMP1053', 12, 8, 20.0, 3, 0, 0),
    ('EMP1054', 12, 8, 20.0, 3, 0, 0),
    ('EMP1055', 12, 8, 20.0, 3, 0, 0),
    ('EMP1056', 12, 8, 20.0, 3, 0, 0),
    ('EMP1057', 12, 8, 20.0, 3, 0, 0),
    ('EMP1058', 12, 8, 20.0, 3, 0, 0),
    ('EMP1059', 12, 8, 20.0, 3, 0, 0),
    ('EMP1060', 12, 8, 20.0, 3, 0, 0),
    ('EMP1061', 12, 8, 20.0, 3, 0, 0),
    ('EMP1062', 12, 8, 20.0, 3, 0, 0),
    ('EMP1063', 12, 8, 20.0, 3, 0, 0),
    ('EMP1064', 12, 8, 20.0, 3, 0, 0),
    ('EMP1065', 12, 8, 20.0, 3, 0, 0),
    ('EMP1066', 12, 8, 20.0, 3, 0, 0),
    ('EMP1067', 12, 8, 20.0, 3, 0, 0),
    ('EMP1068', 12, 8, 20.0, 3, 0, 0),
    ('EMP1069', 12, 8, 20.0, 3, 0, 0),
    ('EMP1070', 12, 8, 20.0, 3, 0, 0),
    ('EMP1071', 12, 8, 20.0, 3, 0, 0),
    ('EMP1072', 12, 8, 20.0, 3, 0, 0),
    ('EMP1073', 12, 8, 20.0, 3, 0, 0),
    ('EMP1074', 12, 8, 20.0, 3, 0, 0),
    ('EMP1075', 12, 8, 20.0, 3, 0, 0),
    ('EMP1076', 12, 8, 20.0, 3, 0, 0),
    ('EMP1077', 12, 8, 20.0, 3, 0, 0),
    ('EMP1078', 12, 8, 20.0, 3, 0, 0),
    ('EMP1079', 12, 8, 20.0, 3, 0, 0),
    ('EMP1080', 12, 8, 20.0, 3, 0, 0),
    ('EMP1081', 12, 8, 20.0, 3, 0, 0),
    ('EMP1082', 12, 8, 20.0, 3, 0, 0),
    ('EMP1083', 12, 8, 20.0, 3, 0, 0),
    ('EMP1084', 12, 8, 20.0, 3, 0, 0),
    ('EMP1085', 12, 8, 20.0, 3, 0, 0),
    ('EMP1086', 12, 8, 20.0, 3, 0, 0),
    ('EMP1087', 12, 8, 20.0, 3, 0, 0),
    ('EMP1088', 12, 8, 20.0, 3, 0, 0),
    ('EMP1089', 12, 8, 20.0, 3, 0, 0),
    ('EMP1090', 12, 8, 20.0, 3, 0, 0),
    ('EMP1091', 12, 8, 20.0, 3, 0, 0),
    ('EMP1092', 12, 8, 20.0, 3, 0, 0),
    ('EMP1093', 12, 8, 20.0, 3, 0, 0),
    ('EMP1094', 12, 8, 20.0, 3, 0, 0),
    ('EMP1095', 12, 8, 20.0, 3, 0, 0),
    ('EMP1096', 12, 8, 20.0, 3, 0, 0),
    ('EMP1097', 12, 8, 20.0, 3, 0, 0),
    ('EMP1098', 12, 8, 20.0, 3, 0, 0),
    ('EMP1099', 12, 8, 20.0, 3, 0, 0)
ON CONFLICT (employee_id) DO NOTHING;

INSERT INTO leave_balance (employee_id, casual_leave, sick_leave, earned_leave, bereavement_leave, marriage_leave, lop_leave) VALUES
    ('EMP1100', 12, 8, 20.0, 3, 0, 0),
    ('EMP1101', 12, 8, 20.0, 3, 0, 0),
    ('EMP1102', 12, 8, 20.0, 3, 0, 0),
    ('EMP1103', 12, 8, 20.0, 3, 0, 0),
    ('EMP1104', 12, 8, 20.0, 3, 0, 0),
    ('EMP1105', 12, 8, 20.0, 3, 0, 0),
    ('EMP1106', 12, 8, 20.0, 3, 0, 0),
    ('EMP1107', 12, 8, 20.0, 3, 0, 0),
    ('EMP1108', 12, 8, 20.0, 3, 0, 0),
    ('EMP1109', 12, 8, 20.0, 3, 0, 0),
    ('EMP1110', 12, 8, 20.0, 3, 0, 0),
    ('EMP1111', 12, 8, 20.0, 3, 0, 0),
    ('EMP1112', 12, 8, 20.0, 3, 0, 0),
    ('EMP1113', 12, 8, 20.0, 3, 0, 0),
    ('EMP1114', 12, 8, 20.0, 3, 0, 0),
    ('EMP1115', 12, 8, 20.0, 3, 0, 0),
    ('EMP1116', 12, 8, 20.0, 3, 0, 0),
    ('EMP1117', 12, 8, 20.0, 3, 0, 0),
    ('EMP1118', 12, 8, 20.0, 3, 0, 0),
    ('EMP1119', 12, 8, 20.0, 3, 0, 0),
    ('EMP1120', 12, 8, 20.0, 3, 0, 0),
    ('EMP1121', 12, 8, 20.0, 3, 0, 0),
    ('EMP1122', 12, 8, 20.0, 3, 0, 0),
    ('EMP1123', 12, 8, 20.0, 3, 0, 0),
    ('EMP1124', 12, 8, 20.0, 3, 0, 0),
    ('EMP1125', 12, 8, 20.0, 3, 0, 0),
    ('EMP1126', 12, 8, 20.0, 3, 0, 0),
    ('EMP1127', 12, 8, 20.0, 3, 0, 0),
    ('EMP1128', 12, 8, 20.0, 3, 0, 0),
    ('EMP1129', 12, 8, 20.0, 3, 0, 0),
    ('EMP1130', 12, 8, 20.0, 3, 0, 0),
    ('EMP1131', 12, 8, 20.0, 3, 0, 0),
    ('EMP1132', 12, 8, 20.0, 3, 0, 0),
    ('EMP1133', 12, 8, 20.0, 3, 0, 0),
    ('EMP1134', 12, 8, 20.0, 3, 0, 0),
    ('EMP1135', 12, 8, 20.0, 3, 0, 0),
    ('EMP1136', 12, 8, 20.0, 3, 0, 0),
    ('EMP1137', 12, 8, 20.0, 3, 0, 0),
    ('EMP1138', 12, 8, 20.0, 3, 0, 0),
    ('EMP1139', 12, 8, 20.0, 3, 0, 0),
    ('EMP1140', 12, 8, 20.0, 3, 0, 0),
    ('EMP1141', 12, 8, 20.0, 3, 0, 0),
    ('EMP1142', 12, 8, 20.0, 3, 0, 0),
    ('EMP1143', 12, 8, 20.0, 3, 0, 0),
    ('EMP1144', 12, 8, 20.0, 3, 0, 0),
    ('EMP1145', 12, 8, 20.0, 3, 0, 0),
    ('EMP1146', 12, 8, 20.0, 3, 0, 0),
    ('EMP1147', 12, 8, 20.0, 3, 0, 0),
    ('EMP1148', 12, 8, 20.0, 3, 0, 0),
    ('EMP1149', 12, 8, 20.0, 3, 0, 0)
ON CONFLICT (employee_id) DO NOTHING;

INSERT INTO leave_balance (employee_id, casual_leave, sick_leave, earned_leave, bereavement_leave, marriage_leave, lop_leave) VALUES
    ('EMP1150', 12, 8, 20.0, 3, 0, 0),
    ('EMP1151', 12, 8, 20.0, 3, 0, 0),
    ('EMP1152', 12, 8, 20.0, 3, 0, 0),
    ('EMP1153', 12, 8, 20.0, 3, 0, 0),
    ('EMP1154', 12, 8, 20.0, 3, 0, 0),
    ('EMP1155', 12, 8, 20.0, 3, 0, 0),
    ('EMP1156', 12, 8, 20.0, 3, 0, 0),
    ('EMP1157', 12, 8, 20.0, 3, 0, 0),
    ('EMP1158', 12, 8, 20.0, 3, 0, 0),
    ('EMP1159', 12, 8, 20.0, 3, 0, 0),
    ('EMP1160', 12, 8, 20.0, 3, 0, 0),
    ('EMP1161', 12, 8, 20.0, 3, 0, 0),
    ('EMP1162', 12, 8, 20.0, 3, 0, 0),
    ('EMP1163', 12, 8, 20.0, 3, 0, 0),
    ('EMP1164', 12, 8, 20.0, 3, 0, 0),
    ('EMP1165', 12, 8, 20.0, 3, 0, 0),
    ('EMP1166', 12, 8, 20.0, 3, 0, 0),
    ('EMP1167', 12, 8, 20.0, 3, 0, 0),
    ('EMP1168', 12, 8, 20.0, 3, 0, 0),
    ('EMP1169', 12, 8, 20.0, 3, 0, 0),
    ('EMP1170', 12, 8, 20.0, 3, 0, 0),
    ('EMP1171', 12, 8, 20.0, 3, 0, 0),
    ('EMP1172', 12, 8, 20.0, 3, 0, 0),
    ('EMP1173', 12, 8, 20.0, 3, 0, 0),
    ('EMP1174', 12, 8, 20.0, 3, 0, 0),
    ('EMP1175', 12, 8, 20.0, 3, 0, 0),
    ('EMP1176', 12, 8, 20.0, 3, 0, 0),
    ('EMP1177', 12, 8, 20.0, 3, 0, 0),
    ('EMP1178', 12, 8, 20.0, 3, 0, 0),
    ('EMP1179', 12, 8, 20.0, 3, 0, 0),
    ('EMP1180', 12, 8, 20.0, 3, 0, 0),
    ('EMP1181', 12, 8, 20.0, 3, 0, 0),
    ('EMP1182', 12, 8, 20.0, 3, 0, 0),
    ('EMP1183', 12, 8, 20.0, 3, 0, 0),
    ('EMP1184', 12, 8, 20.0, 3, 0, 0),
    ('EMP1185', 12, 8, 20.0, 3, 0, 0),
    ('EMP1186', 12, 8, 20.0, 3, 0, 0),
    ('EMP1187', 12, 8, 20.0, 3, 0, 0),
    ('EMP1188', 12, 8, 20.0, 3, 0, 0),
    ('EMP1189', 12, 8, 20.0, 3, 0, 0),
    ('EMP1190', 12, 8, 20.0, 3, 0, 0),
    ('EMP1191', 12, 8, 20.0, 3, 0, 0),
    ('EMP1192', 12, 8, 20.0, 3, 0, 0),
    ('EMP1193', 12, 8, 20.0, 3, 0, 0),
    ('EMP1194', 12, 8, 20.0, 3, 0, 0),
    ('EMP1195', 12, 8, 20.0, 3, 0, 0),
    ('EMP1196', 12, 8, 20.0, 3, 0, 0),
    ('EMP1197', 12, 8, 20.0, 3, 0, 0),
    ('EMP1198', 12, 8, 20.0, 3, 0, 0),
    ('EMP1199', 12, 8, 20.0, 3, 0, 0)
ON CONFLICT (employee_id) DO NOTHING;

INSERT INTO leave_balance (employee_id, casual_leave, sick_leave, earned_leave, bereavement_leave, marriage_leave, lop_leave) VALUES
    ('EMP1200', 12, 8, 20.0, 3, 0, 0),
    ('EMP1201', 12, 8, 20.0, 3, 0, 0),
    ('EMP1202', 12, 8, 20.0, 3, 0, 0),
    ('EMP1203', 12, 8, 20.0, 3, 0, 0),
    ('EMP1204', 12, 8, 20.0, 3, 0, 0),
    ('EMP1205', 12, 8, 20.0, 3, 0, 0),
    ('EMP1206', 12, 8, 20.0, 3, 0, 0),
    ('EMP1207', 12, 8, 20.0, 3, 0, 0),
    ('EMP1208', 12, 8, 20.0, 3, 0, 0),
    ('EMP1209', 12, 8, 20.0, 3, 0, 0),
    ('EMP1210', 12, 8, 20.0, 3, 0, 0),
    ('EMP1211', 12, 8, 20.0, 3, 0, 0),
    ('EMP1212', 12, 8, 20.0, 3, 0, 0),
    ('EMP1213', 12, 8, 20.0, 3, 0, 0),
    ('EMP1214', 12, 8, 20.0, 3, 0, 0),
    ('EMP1215', 12, 8, 20.0, 3, 0, 0),
    ('EMP1216', 12, 8, 20.0, 3, 0, 0),
    ('EMP1217', 12, 8, 20.0, 3, 0, 0),
    ('EMP1218', 12, 8, 20.0, 3, 0, 0),
    ('EMP1219', 12, 8, 20.0, 3, 0, 0),
    ('EMP1220', 12, 8, 20.0, 3, 0, 0),
    ('EMP1221', 12, 8, 20.0, 3, 0, 0),
    ('EMP1222', 12, 8, 20.0, 3, 0, 0),
    ('EMP1223', 12, 8, 20.0, 3, 0, 0),
    ('EMP1224', 12, 8, 20.0, 3, 0, 0),
    ('EMP1225', 12, 8, 20.0, 3, 0, 0),
    ('EMP1226', 12, 8, 20.0, 3, 0, 0),
    ('EMP1227', 12, 8, 20.0, 3, 0, 0),
    ('EMP1228', 12, 8, 20.0, 3, 0, 0),
    ('EMP1229', 12, 8, 20.0, 3, 0, 0),
    ('EMP1230', 12, 8, 20.0, 3, 0, 0),
    ('EMP1231', 12, 8, 20.0, 3, 0, 0),
    ('EMP1232', 12, 8, 20.0, 3, 0, 0),
    ('EMP1233', 12, 8, 20.0, 3, 0, 0),
    ('EMP1234', 12, 8, 20.0, 3, 0, 0),
    ('EMP1235', 12, 8, 20.0, 3, 0, 0),
    ('EMP1236', 12, 8, 20.0, 3, 0, 0),
    ('EMP1237', 12, 8, 20.0, 3, 0, 0),
    ('EMP1238', 12, 8, 20.0, 3, 0, 0),
    ('EMP1239', 12, 8, 20.0, 3, 0, 0),
    ('EMP1240', 12, 8, 20.0, 3, 0, 0),
    ('EMP1241', 12, 8, 20.0, 3, 0, 0),
    ('EMP1242', 12, 8, 20.0, 3, 0, 0),
    ('EMP1243', 12, 8, 20.0, 3, 0, 0),
    ('EMP1244', 12, 8, 20.0, 3, 0, 0),
    ('EMP1245', 12, 8, 20.0, 3, 0, 0),
    ('EMP1246', 12, 8, 20.0, 3, 0, 0),
    ('EMP1247', 12, 8, 20.0, 3, 0, 0),
    ('EMP1248', 12, 8, 20.0, 3, 0, 0),
    ('EMP1249', 12, 8, 20.0, 3, 0, 0)
ON CONFLICT (employee_id) DO NOTHING;

INSERT INTO leave_balance (employee_id, casual_leave, sick_leave, earned_leave, bereavement_leave, marriage_leave, lop_leave) VALUES
    ('EMP1250', 12, 8, 20.0, 3, 0, 0),
    ('EMP1251', 12, 8, 20.0, 3, 0, 0),
    ('EMP1252', 12, 8, 20.0, 3, 0, 0),
    ('EMP1253', 12, 8, 20.0, 3, 0, 0),
    ('EMP1254', 12, 8, 20.0, 3, 0, 0),
    ('EMP1255', 12, 8, 20.0, 3, 0, 0),
    ('EMP1256', 12, 8, 20.0, 3, 0, 0)
ON CONFLICT (employee_id) DO NOTHING;

-- ─────────────────────────────────────────────────────────
-- 6. SEED SAMPLE ATTENDANCE RECORDS (For Live Dashboard & Radar)
-- ─────────────────────────────────────────────────────────
INSERT INTO attendance_logs (employee_id, attendance_date, check_in_time, check_out_time, check_in_latitude, check_in_longitude, check_in_location, is_wfh, working_hours, status, is_late, location_verified) VALUES
    ('OTSI0001', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1001', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1000', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1003', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1004', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1005', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1006', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1007', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1008', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1009', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1010', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1011', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1012', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1013', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1014', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1015', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1016', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1017', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1018', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1019', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1020', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1021', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1022', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1023', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1024', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1025', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1026', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1027', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1028', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1029', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1030', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1031', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1032', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1033', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1034', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1035', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1036', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1037', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1038', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1039', '2026-10-27', '2026-10-27T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE),
    ('EMP1040', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE),
    ('EMP1041', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE),
    ('EMP1042', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE),
    ('EMP1043', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE),
    ('EMP1044', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE),
    ('EMP1045', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE),
    ('EMP1046', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE),
    ('EMP1047', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE),
    ('EMP1048', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE),
    ('EMP1049', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE),
    ('EMP1050', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE),
    ('EMP1051', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE),
    ('EMP1052', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE),
    ('EMP1053', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE),
    ('EMP1054', '2026-10-27', '2026-10-27T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE)
ON CONFLICT (employee_id, attendance_date) DO NOTHING;

-- ─────────────────────────────────────────────────────────
-- 7. ORG HIERARCHY RECURSIVE VIEW
-- ─────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW v_org_tree AS
WITH RECURSIVE org_hierarchy AS (
    -- Anchor: Top leaders with no manager
    SELECT 
        employee_id, full_name, designation, department, team, manager_id, manager_name, role,
        1 as level,
        ARRAY[full_name::text] as path
    FROM employees
    WHERE manager_id IS NULL AND status = 'active'
    
    UNION ALL
    
    -- Recursive step: Direct reportees
    SELECT 
        e.employee_id, e.full_name, e.designation, e.department, e.team, e.manager_id, e.manager_name, e.role,
        h.level + 1,
        h.path || e.full_name::text
    FROM employees e
    INNER JOIN org_hierarchy h ON e.manager_id = h.employee_id
    WHERE e.status = 'active'
)
SELECT * FROM org_hierarchy ORDER BY level, department, full_name;
