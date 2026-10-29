-- ============================================================
-- OTSI Attendance Portal - Complete Unified Schema (Supabase/PostgreSQL)
-- Schema: public
-- ============================================================

-- ─────────────────────────────────────────────────────────
-- 1. Employees Table
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    designation VARCHAR(100),
    department VARCHAR(100),
    team VARCHAR(100),
    department_id INT,
    team_id INT,
    client_id INT,
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
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_temp_code VARCHAR(6),
    mfa_temp_expires TIMESTAMP
);

-- ─────────────────────────────────────────────────────────
-- 2. Attendance Logs Table
-- ─────────────────────────────────────────────────────────
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

-- ─────────────────────────────────────────────────────────
-- 3. Leave Balance Table
-- ─────────────────────────────────────────────────────────
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

-- ─────────────────────────────────────────────────────────
-- 4. Leave Applications Table
-- ─────────────────────────────────────────────────────────
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

-- ─────────────────────────────────────────────────────────
-- 5. Timesheet Table
-- ─────────────────────────────────────────────────────────
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

-- ─────────────────────────────────────────────────────────
-- 6. Timesheet Entries Table
-- ─────────────────────────────────────────────────────────
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

-- ─────────────────────────────────────────────────────────
-- 7. Help Desk Tickets Table
-- ─────────────────────────────────────────────────────────
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

-- ─────────────────────────────────────────────────────────
-- 8. Notifications Table
-- ─────────────────────────────────────────────────────────
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

-- ─────────────────────────────────────────────────────────
-- 9. Audit Logs Table
-- ─────────────────────────────────────────────────────────
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

-- ─────────────────────────────────────────────────────────
-- 10. Password History Table
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS password_history (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────────────────
-- 11. Clients Table
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    contact_person VARCHAR(150),
    contact_email VARCHAR(100),
    contact_phone VARCHAR(20),
    location VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────────────────
-- 12. Departments Table
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    manager_id VARCHAR(50),
    hr_manager_id VARCHAR(50),
    location VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id) ON DELETE SET NULL,
    FOREIGN KEY (hr_manager_id) REFERENCES employees(employee_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────────────────
-- 13. Teams Table
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    department_id INT NOT NULL,
    team_lead_id VARCHAR(50),
    hr_manager_id VARCHAR(50),
    description TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, department_id),
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
    FOREIGN KEY (team_lead_id) REFERENCES employees(employee_id) ON DELETE SET NULL,
    FOREIGN KEY (hr_manager_id) REFERENCES employees(employee_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────────────────
-- 14. Projects Table
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    client_id INT,
    team_id INT,
    project_lead_id VARCHAR(50),
    description TEXT,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'on_hold', 'completed', 'archived')),
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (project_lead_id) REFERENCES employees(employee_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────────────────
-- 15. Employee Teams Junction Table
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employee_teams (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    team_id INT NOT NULL,
    role VARCHAR(50),
    assigned_date DATE DEFAULT CURRENT_DATE,
    end_date DATE,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, team_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────
-- 16. Attendance Corrections Table
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attendance_corrections (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    attendance_date DATE NOT NULL,
    correction_type VARCHAR(50) NOT NULL CHECK (correction_type IN ('check_in', 'check_out', 'status', 'full_day')),
    old_check_in_time TIMESTAMP,
    new_check_in_time TIMESTAMP,
    old_check_out_time TIMESTAMP,
    new_check_out_time TIMESTAMP,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    reason TEXT NOT NULL,
    requested_by VARCHAR(50) NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled')),
    approved_by VARCHAR(50),
    approval_comments TEXT,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
    FOREIGN KEY (requested_by) REFERENCES employees(employee_id) ON DELETE SET NULL,
    FOREIGN KEY (approved_by) REFERENCES employees(employee_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────────────────
-- 17. New Employee Requests Table
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS new_employee_requests (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    designation VARCHAR(100),
    department_id INT,
    team_id INT,
    manager_id VARCHAR(50),
    date_of_joining DATE,
    reason TEXT,
    requested_by VARCHAR(50),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled')),
    approved_by VARCHAR(50),
    approval_comments TEXT,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL,
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id) ON DELETE SET NULL,
    FOREIGN KEY (requested_by) REFERENCES employees(employee_id) ON DELETE SET NULL,
    FOREIGN KEY (approved_by) REFERENCES employees(employee_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────────────────
-- 18. Approval Workflows Table
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS approval_workflows (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('leave', 'attendance_correction', 'new_employee', 'expense', 'request')),
    entity_id INT NOT NULL,
    current_approver_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'escalated')),
    approval_level INT DEFAULT 1,
    max_approval_level INT DEFAULT 2,
    approval_date TIMESTAMP,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (current_approver_id) REFERENCES employees(employee_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────────────────
-- Performance Indexes
-- ─────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_attendance_logs_employee_id ON attendance_logs(employee_id);
CREATE INDEX IF NOT EXISTS idx_attendance_logs_date ON attendance_logs(attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_logs_employee_date ON attendance_logs(employee_id, attendance_date);
CREATE INDEX IF NOT EXISTS idx_leave_applications_employee_id ON leave_applications(employee_id);
CREATE INDEX IF NOT EXISTS idx_leave_applications_status ON leave_applications(status);
CREATE INDEX IF NOT EXISTS idx_timesheets_employee_id ON timesheets(employee_id);
CREATE INDEX IF NOT EXISTS idx_timesheets_status ON timesheets(status);
CREATE INDEX IF NOT EXISTS idx_support_tickets_employee_id ON support_tickets(employee_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_notifications_employee_id ON notifications(employee_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);

-- ─────────────────────────────────────────────────────────
-- Disable Row Level Security (Allows backend operations with API key)
-- ─────────────────────────────────────────────────────────
ALTER TABLE IF EXISTS employees DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS attendance_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS leave_balance DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS leave_applications DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS timesheets DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS timesheet_entries DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS support_tickets DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS password_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS clients DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS departments DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS teams DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS projects DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS employee_teams DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS attendance_corrections DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS new_employee_requests DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS approval_workflows DISABLE ROW LEVEL SECURITY;

-- ─────────────────────────────────────────────────────────
-- Seed Super Admin & Core Sample Accounts
-- Default Password: M@llem5831!
-- ─────────────────────────────────────────────────────────
INSERT INTO employees (employee_id, email, full_name, designation, department, team, role, status, password_hash)
VALUES
    ('OTSI0001', 'admin.otsi@otsi-usa.com', 'OTSI Administrator', 'System Administrator', 'Administration', 'Core Admin', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de'),
    ('EMP1000', 'kiran.us009@gmail.com', 'Ravi Kiran', 'Executive Director', 'Executive', 'Leadership', 'admin', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de'),
    ('EMP1001', 'ravi.mallem@otsi.co.in', 'Ravi Mallem', 'Senior Software Engineer', 'Engineering', 'Full Stack', 'employee', 'active', 'pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de')
ON CONFLICT (employee_id) DO UPDATE 
SET password_hash = EXCLUDED.password_hash,
    status = 'active';

INSERT INTO leave_balance (employee_id, casual_leave, sick_leave, earned_leave, bereavement_leave, marriage_leave, lop_leave)
VALUES
    ('OTSI0001', 12, 8, 20.0, 3, 0, 0),
    ('EMP1000', 12, 8, 20.0, 3, 0, 0),
    ('EMP1001', 12, 8, 20.0, 3, 0, 0)
ON CONFLICT (employee_id) DO NOTHING;
