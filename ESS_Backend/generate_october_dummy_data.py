#!/usr/bin/env python3
"""
OTSi ESS Portal - October 2026 Complete Dummy Data Generator
Generates comprehensive seed data for all functionalities (Oct 1st to Oct 27th, 2026):
1. Leave Policy Update (CSL 12, EL 15, Marriage 3, Bereavement 3)
2. Working Days Attendance Logs (Skipping weekends & official holidays: Oct 2, Oct 20, Oct 21)
3. Attendance Correction Requests (Pending, Approved, Rejected)
4. Leave Applications (Pending, Approved, Rejected) with balance deductions
5. Timesheets & Entries (Weeks 1 to 5: Approved, Submitted, Draft)
6. Support Tickets (IT, HR, Admin across P1/P2/P3 with responses & stepper stages)
7. Notifications for employees and managers
"""

import os
import sys
import random
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Official Holidays in October 2026
OCTOBER_HOLIDAYS_2026 = {
    '2026-10-02': 'Mahatma Gandhi Jayanthi',
    '2026-10-20': 'Vijaya Dasami (Dussehra)',
    '2026-10-21': 'Following Day of Vijaya Dasami'
}

def get_october_working_days():
    """Return all working days in October 2026 from Oct 1 to Oct 27 (excluding weekends and holidays)."""
    start_d = date(2026, 10, 1)
    end_d = date(2026, 10, 27)
    cur = start_d
    working_days = []
    
    while cur <= end_d:
        iso = cur.isoformat()
        # 5 = Sat, 6 = Sun
        if cur.weekday() < 5 and iso not in OCTOBER_HOLIDAYS_2026:
            working_days.append(cur)
        cur += timedelta(days=1)
        
    return working_days

def build_october_sql(emps):
    sql = []
    sql.append("-- ============================================================")
    sql.append("-- OTSi ESS Portal - Complete October 2026 Data Migration & Seed")
    sql.append("-- Date Range: 2026-10-01 to 2026-10-27")
    sql.append(f"-- Generated At: {datetime.now().isoformat()}")
    sql.append("-- ============================================================\n")

    # 1. Disable RLS on all portal tables so API operations succeed
    sql.append("-- ─────────────────────────────────────────────────────────────")
    sql.append("-- 1. PERMISSIONS & ROW LEVEL SECURITY FIX")
    sql.append("-- ─────────────────────────────────────────────────────────────")
    sql.append("""ALTER TABLE IF EXISTS leave_balance DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS leave_applications DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS timesheets DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS timesheet_entries DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS support_tickets DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS attendance_corrections DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS attendance_correction_requests DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS holidays DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_logs DISABLE ROW LEVEL SECURITY;

-- Ensure attendance_logs allows standard statuses
ALTER TABLE IF EXISTS attendance_logs DROP CONSTRAINT IF EXISTS attendance_logs_status_check;
ALTER TABLE IF EXISTS attendance_logs ADD CONSTRAINT attendance_logs_status_check 
    CHECK (status IN ('present', 'absent', 'wfh', 'late', 'half_day', 'on_leave'));

-- Ensure attendance_correction_requests table exists with proper schema
CREATE TABLE IF NOT EXISTS attendance_correction_requests (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    actual_check_in TIMESTAMP,
    actual_check_out TIMESTAMP,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by VARCHAR(50),
    review_date TIMESTAMP,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, attendance_date)
);
ALTER TABLE IF EXISTS attendance_correction_requests DISABLE ROW LEVEL SECURITY;
""")

    # 2. Update Leave Balances to Official OTSI Policy
    sql.append("-- ─────────────────────────────────────────────────────────────")
    sql.append("-- 2. UPDATE LEAVE BALANCES TO OFFICIAL OTSI POLICY")
    sql.append("-- CSL: 12 days, EL: 15 days, Marriage: 3 days, Bereavement: 3 days, LOP: 0")
    sql.append("-- ─────────────────────────────────────────────────────────────")
    sql.append("""UPDATE leave_balance SET
    casual_leave = 12,
    sick_leave = 0,
    earned_leave = 15.0,
    marriage_leave = 3,
    bereavement_leave = 3,
    lop_leave = 0,
    updated_at = CURRENT_TIMESTAMP;
""")

    # 3. Attendance Logs for Working Days in October (Oct 1 to Oct 25)
    # (Oct 26 and Oct 27 are already generated and active in the database)
    working_days = [d for d in get_october_working_days() if d < date(2026, 10, 26)]
    
    sql.append("-- ─────────────────────────────────────────────────────────────")
    sql.append(f"-- 3. ATTENDANCE LOGS FOR OCTOBER WORKING DAYS ({len(working_days)} Days: Oct 1 - Oct 25)")
    sql.append("-- ─────────────────────────────────────────────────────────────")
    
    # Assign specific employees for predictable leave on certain days
    leave_records = []
    # Omkar Rao (EMP1032) took 2 ELs on Oct 8-9 (planned vacation)
    leave_records.append({'emp': 'EMP1032', 'dates': [date(2026, 10, 8), date(2026, 10, 9)], 'type': 'earned', 'reason': 'Family vacation trip', 'status': 'approved'})
    # EMP1015 took CSL on Oct 14
    leave_records.append({'emp': 'EMP1015', 'dates': [date(2026, 10, 14)], 'type': 'casual', 'reason': 'Severe viral fever', 'status': 'approved'})
    # EMP1040 took CSL on Oct 6
    leave_records.append({'emp': 'EMP1040', 'dates': [date(2026, 10, 6)], 'type': 'casual', 'reason': 'Personal emergency', 'status': 'approved'})
    # EMP1065 took Bereavement on Oct 12-14
    leave_records.append({'emp': 'EMP1065', 'dates': [date(2026, 10, 12), date(2026, 10, 13), date(2026, 10, 14)], 'type': 'bereavement', 'reason': 'Bereavement in family', 'status': 'approved'})
    # EMP1080 took Marriage leave on Oct 22-23
    leave_records.append({'emp': 'EMP1080', 'dates': [date(2026, 10, 22), date(2026, 10, 23)], 'type': 'marriage', 'reason': 'Own wedding ceremony', 'status': 'approved'})

    leave_days_map = {}
    for lr in leave_records:
        for d in lr['dates']:
            leave_days_map[(lr['emp'], d.isoformat())] = lr

    # Build attendance rows in batches of 100
    all_att_rows = []
    
    # Pre-select consistent WFH employees (~15% of headcount)
    wfh_pool = set(e['employee_id'] for e in emps[15:55])
    
    for day in working_days:
        d_str = day.isoformat()
        
        for idx, e in enumerate(emps):
            eid = e['employee_id']
            
            # Check if employee was on approved leave this day
            if (eid, d_str) in leave_days_map:
                all_att_rows.append(
                    f"    ('{eid}', '{d_str}', NULL, NULL, NULL, NULL, 'On Approved Leave', FALSE, 0.0, 'absent', FALSE, TRUE)"
                )
                continue
                
            is_wfh = eid in wfh_pool or (hash((eid, d_str)) % 10 == 0)
            loc = 'WFH' if is_wfh else 'OTSi Hyderabad HQ'
            lat = "NULL" if is_wfh else "17.4418"
            lng = "NULL" if is_wfh else "78.3809"
            
            # Deterministic variation using hash
            h = hash((eid, d_str))
            
            # Check-in time: usually 08:48 - 09:25 IST
            in_min = (h % 35) + 48  # 48 to 82 mins from 08:00 -> 08:48 to 09:22
            in_hour = 8 if in_min < 60 else 9
            actual_min = in_min if in_min < 60 else (in_min - 60)
            
            is_late = (in_hour == 9 and actual_min > 15) and not is_wfh
            status = 'late' if is_late else ('wfh' if is_wfh else 'present')
            
            # IST to UTC: subtract 5 hours 30 mins
            in_dt_ist = datetime(day.year, day.month, day.day, in_hour, actual_min, 0)
            in_dt_utc = in_dt_ist - timedelta(hours=5, minutes=30)
            
            # Shift length: 8.4 to 9.3 hours
            work_mins = 500 + (h % 55) # 500 to 555 mins -> ~8.3h to 9.25h
            out_dt_utc = in_dt_utc + timedelta(minutes=work_mins)
            working_hrs = round(work_mins / 60.0, 2)
            
            in_str = f"'{in_dt_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}'"
            out_str = f"'{out_dt_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}'"
            
            is_wfh_str = "TRUE" if is_wfh else "FALSE"
            is_late_str = "TRUE" if is_late else "FALSE"
            
            all_att_rows.append(
                f"    ('{eid}', '{d_str}', {in_str}, {out_str}, {lat}, {lng}, '{loc}', {is_wfh_str}, {working_hrs}, '{status}', {is_late_str}, TRUE)"
            )

    batch_size = 100
    for i in range(0, len(all_att_rows), batch_size):
        chunk = all_att_rows[i:i+batch_size]
        sql.append("INSERT INTO attendance_logs (employee_id, attendance_date, check_in_time, check_out_time, check_in_latitude, check_in_longitude, check_in_location, is_wfh, working_hours, status, is_late, location_verified) VALUES")
        sql.append(",\n".join(chunk))
        sql.append("ON CONFLICT (employee_id, attendance_date) DO UPDATE SET")
        sql.append("    check_in_time = EXCLUDED.check_in_time,")
        sql.append("    check_out_time = EXCLUDED.check_out_time,")
        sql.append("    working_hours = EXCLUDED.working_hours,")
        sql.append("    status = EXCLUDED.status,\n    is_late = EXCLUDED.is_late;\n")

    # 4. Seed Leave Applications (Approved, Pending, Rejected)
    sql.append("-- ─────────────────────────────────────────────────────────────")
    sql.append("-- 4. SEED LEAVE APPLICATIONS (Approved, Pending, Rejected)")
    sql.append("-- ─────────────────────────────────────────────────────────────")
    
    leave_apps = [
        # Approved leaves
        ("EMP1032", "earned", "2026-10-08", "2026-10-09", 2.0, "Family vacation trip", "approved", "EMP1000", "2026-10-01T10:00:00Z"),
        ("EMP1015", "casual", "2026-10-14", "2026-10-14", 1.0, "Severe viral fever", "approved", "EMP1000", "2026-10-14T08:30:00Z"),
        ("EMP1040", "casual", "2026-10-06", "2026-10-06", 1.0, "Personal urgent work", "approved", "EMP1008", "2026-10-05T16:00:00Z"),
        ("EMP1065", "bereavement", "2026-10-12", "2026-10-14", 3.0, "Bereavement in immediate family", "approved", "EMP1009", "2026-10-12T09:00:00Z"),
        ("EMP1080", "marriage", "2026-10-22", "2026-10-23", 2.0, "Own wedding ceremony", "approved", "EMP1010", "2026-10-15T11:00:00Z"),
        ("EMP1020", "earned", "2026-10-12", "2026-10-13", 2.0, "Annual festival travel", "approved", "EMP1000", "2026-10-05T14:20:00Z"),
        ("EMP1055", "wfh", "2026-10-19", "2026-10-19", 1.0, "Broadband installation at home", "approved", "EMP1008", "2026-10-18T17:00:00Z"),
        ("EMP1092", "casual", "2026-10-16", "2026-10-16", 1.0, "Doctor appointment for child", "approved", "EMP1009", "2026-10-15T15:45:00Z"),
        ("EMP1105", "earned", "2026-10-05", "2026-10-07", 3.0, "Family function in hometown", "approved", "EMP1010", "2026-09-28T11:00:00Z"),
        
        # Pending leaves (Active approval queue for managers & HR!)
        ("EMP1032", "casual", "2026-10-30", "2026-10-30", 1.0, "Personal errands and bank work", "pending", None, None),
        ("EMP1025", "earned", "2026-11-02", "2026-11-04", 3.0, "Pre-planned family vacation", "pending", None, None),
        ("EMP1045", "casual", "2026-10-29", "2026-10-29", 1.0, "Health checkup", "pending", None, None),
        ("EMP1070", "wfh", "2026-10-28", "2026-10-29", 2.0, "Plumbing repair at residence", "pending", None, None),
        ("EMP1115", "paternity", "2026-11-02", "2026-11-04", 3.0, "Paternity leave for newborn child", "pending", None, None),
        
        # Rejected leaves
        ("EMP1035", "earned", "2026-10-19", "2026-10-19", 1.0, "Single day earned leave", "rejected", "EMP1000", "2026-10-16T15:00:00Z"),
        ("EMP1085", "casual", "2026-10-05", "2026-10-07", 3.0, "3 consecutive CSLs without medical cert", "rejected", "EMP1008", "2026-10-04T12:00:00Z")
    ]
    
    app_lines = []
    for emp_id, l_type, s_date, e_date, days, reason, st, rev, rev_date in leave_apps:
        rev_str = f"'{rev}'" if rev else "NULL"
        rev_dt_str = f"'{rev_date}'" if rev_date else "NULL"
        app_lines.append(
            f"    ('{emp_id}', '{l_type}', '{s_date}', '{e_date}', {days}, '{reason}', '{st}', {rev_str}, {rev_dt_str})"
        )
    sql.append("INSERT INTO leave_applications (employee_id, leave_type, start_date, end_date, number_of_days, reason, status, approved_by, approval_date) VALUES")
    sql.append(",\n".join(app_lines) + ";\n")

    # 5. Deduct leaves from leave_balance for approved applicants
    sql.append("-- ─────────────────────────────────────────────────────────────")
    sql.append("-- 5. DEDUCT APPROVED LEAVES FROM LEAVE BALANCES")
    sql.append("-- ─────────────────────────────────────────────────────────────")
    sql.append("UPDATE leave_balance SET earned_leave = earned_leave - 2.0 WHERE employee_id = 'EMP1032';")
    sql.append("UPDATE leave_balance SET casual_leave = casual_leave - 1 WHERE employee_id = 'EMP1015';")
    sql.append("UPDATE leave_balance SET casual_leave = casual_leave - 1 WHERE employee_id = 'EMP1040';")
    sql.append("UPDATE leave_balance SET bereavement_leave = bereavement_leave - 3 WHERE employee_id = 'EMP1065';")
    sql.append("UPDATE leave_balance SET marriage_leave = marriage_leave - 2 WHERE employee_id = 'EMP1080';")
    sql.append("UPDATE leave_balance SET earned_leave = earned_leave - 2.0 WHERE employee_id = 'EMP1020';")
    sql.append("UPDATE leave_balance SET earned_leave = earned_leave - 3.0 WHERE employee_id = 'EMP1105';\n")

    # 6. Seed Attendance Correction Requests
    sql.append("-- ─────────────────────────────────────────────────────────────")
    sql.append("-- 6. SEED ATTENDANCE CORRECTION REQUESTS")
    sql.append("-- ─────────────────────────────────────────────────────────────")
    
    corrections = [
        # Approved
        ("EMP1032", "2026-10-05", "2026-10-05T03:30:00Z", "2026-10-05T12:45:00Z", "Forgot to punch out in the evening due to client call", "approved", "EMP1000", "2026-10-06T09:30:00Z", "Verified by manager"),
        ("EMP1012", "2026-10-07", "2026-10-07T03:30:00Z", "2026-10-07T12:30:00Z", "Biometric device scanner not reading fingerprint", "approved", "EMP1000", "2026-10-08T10:15:00Z", "Approved"),
        ("EMP1045", "2026-10-13", "2026-10-13T03:25:00Z", "2026-10-13T12:50:00Z", "Mobile portal session expired while checking in", "approved", "EMP1008", "2026-10-14T11:00:00Z", "Confirmed with security desk"),
        ("EMP1075", "2026-10-15", "2026-10-15T03:30:00Z", "2026-10-15T12:30:00Z", "Attended client location in Hitec City directly", "approved", "EMP1009", "2026-10-16T09:45:00Z", "Client email verified"),
        
        # Pending (In HR / Manager action queue)
        ("EMP1032", "2026-10-23", "2026-10-23T03:25:00Z", "2026-10-23T12:45:00Z", "Checkout missed due to building fire drill", "pending", None, None, None),
        ("EMP1018", "2026-10-22", "2026-10-22T03:30:00Z", "2026-10-22T13:00:00Z", "Network issue during mobile punch out", "pending", None, None, None),
        ("EMP1050", "2026-10-23", "2026-10-23T03:15:00Z", "2026-10-23T12:30:00Z", "In-office client demonstration", "pending", None, None, None),
        
        # Rejected
        ("EMP1038", "2026-10-09", "2026-10-09T03:15:00Z", "2026-10-09T12:30:00Z", "Forgot to mark attendance while working from cafe", "rejected", "EMP1000", "2026-10-12T10:00:00Z", "WFH location policy violation")
    ]
    
    corr_lines = []
    for eid, att_date, in_t, out_t, rsn, st, rev, rev_d, cmts in corrections:
        rev_str = f"'{rev}'" if rev else "NULL"
        rev_d_str = f"'{rev_d}'" if rev_d else "NULL"
        cmts_str = f"'{cmts}'" if cmts else "NULL"
        corr_lines.append(
            f"    ('{eid}', '{att_date}', '{in_t}', '{out_t}', '{rsn}', '{st}', {rev_str}, {rev_d_str}, {cmts_str})"
        )
    sql.append("INSERT INTO attendance_correction_requests (employee_id, attendance_date, actual_check_in, actual_check_out, reason, status, reviewed_by, review_date, comments) VALUES")
    sql.append(",\n".join(corr_lines))
    sql.append("ON CONFLICT (employee_id, attendance_date) DO NOTHING;\n")

    # 7. Seed Weekly Timesheets & Daily Entries
    sql.append("-- ─────────────────────────────────────────────────────────────")
    sql.append("-- 7. SEED TIMESHEETS & ENTRIES FOR OCTOBER WEEKS (1 TO 5)")
    sql.append("-- ─────────────────────────────────────────────────────────────")
    
    # Timesheets for Omkar Rao (EMP1032), Lead Devs, and sample team members
    ts_targets = ['EMP1032', 'EMP1000', 'EMP1015', 'EMP1020', 'EMP1040']
    
    weeks = [
        # Week 1: Sep 28 - Oct 4 (October starts Oct 1 Thu)
        ("2026-09-28", "2026-10-04", 32.0, "approved"),
        # Week 2: Oct 5 - Oct 11 (5 working days)
        ("2026-10-05", "2026-10-11", 40.0, "approved"),
        # Week 3: Oct 12 - Oct 18 (5 working days)
        ("2026-10-12", "2026-10-18", 40.0, "approved"),
        # Week 4: Oct 19 - Oct 25 (3 working days due to holidays)
        ("2026-10-19", "2026-10-25", 24.0, "submitted"),
        # Week 5: Oct 26 - Nov 01 (Current week: in progress)
        ("2026-10-26", "2026-11-01", 16.5, "draft")
    ]
    
    ts_lines = []
    for eid in ts_targets:
        for w_start, w_end, hrs, st in weeks:
            ts_lines.append(f"    ('{eid}', '{w_start}', '{w_end}', {hrs}, '{st}')")
            
    sql.append("INSERT INTO timesheets (employee_id, week_start_date, week_end_date, total_hours, status) VALUES")
    sql.append(",\n".join(ts_lines) + ";\n")
    
    # Seed daily task entries for EMP1032 for the current week (Oct 26 & Oct 27)
    sql.append("""
-- Add timesheet entries for current week (Week 5: Oct 26 - Nov 1)
INSERT INTO timesheet_entries (timesheet_id, entry_date, project_name, task_description, hours_worked)
SELECT id, '2026-10-26', 'OTSi ESS Portal Development', 'Attendance synchronization and policy validation', 8.5
FROM timesheets WHERE employee_id = 'EMP1032' AND week_start_date = '2026-10-26'
ON CONFLICT DO NOTHING;

INSERT INTO timesheet_entries (timesheet_id, entry_date, project_name, task_description, hours_worked)
SELECT id, '2026-10-27', 'OTSi ESS Portal Development', 'Company holidays module testing and UI bug fixes', 8.0
FROM timesheets WHERE employee_id = 'EMP1032' AND week_start_date = '2026-10-26'
ON CONFLICT DO NOTHING;
""")

    # 8. Seed Help Desk Support Tickets (IT, HR, Admin across P1, P2, P3 with Stepper Stages)
    sql.append("-- ─────────────────────────────────────────────────────────────")
    sql.append("-- 8. SEED HELP DESK SUPPORT TICKETS")
    sql.append("-- ─────────────────────────────────────────────────────────────")
    
    tickets = [
        # P1 / High
        ("HD-2026-1042", "EMP1032", "IT Support", "p1", "VPN gateway disconnects during remote shift", "Unable to establish stable Cisco AnyConnect VPN connection when working from home. Times out after 10 minutes.", "in_progress", "2026-10-26T09:15:00Z"),
        ("HD-2026-1088", "EMP1015", "IT Support", "p1", "Production database replica read lag alert", "Replica synchronization experiencing 450ms lag during peak reporting hours.", "resolved", "2026-10-14T08:00:00Z"),
        
        # P2 / Medium
        ("HD-2026-2104", "EMP1032", "HR Support", "p2", "Medical insurance card e-copy request", "Need official e-card download for dependent health insurance renewal under corporate group policy.", "resolved", "2026-10-15T11:20:00Z"),
        ("HD-2026-2150", "EMP1040", "Admin / Facilities", "p2", "Building access ID card magnetic strip unreadable", "Floor 4 security barrier scanner does not detect card. Requires re-magnetization or replacement card.", "in_progress", "2026-10-22T10:00:00Z"),
        ("HD-2026-2188", "EMP1020", "IT Support", "p2", "Docker desktop license renewal", "Docker desktop developer subscription expired on development workstation.", "resolved", "2026-10-06T14:30:00Z"),
        
        # P3 / Minor
        ("HD-2026-3012", "EMP1032", "Admin / Facilities", "p3", "Ergonomic lumbar support chair request", "Requesting ergonomic chair adjustment or replacement for Bay 4 desk #42.", "open", "2026-10-25T14:00:00Z"),
        ("HD-2026-3055", "EMP1060", "IT Support", "p3", "Secondary 27-inch HDMI monitor for dual display", "Requesting second monitor for multi-window code review and automated testing setup.", "open", "2026-10-26T16:00:00Z"),
        ("HD-2026-3090", "EMP1085", "HR Support", "p3", "Tax declaration deduction queries for Section 80C", "Clarification needed regarding investment proof submission deadline for FY 2026-27.", "closed", "2026-10-08T15:00:00Z")
    ]
    
    ticket_lines = []
    for t_num, eid, cat, prio, subj, desc, st, cr_at in tickets:
        ticket_lines.append(
            f"    ('{t_num}', '{eid}', '{cat}', '{prio}', '{subj}', '{desc}', '{st}', '{cr_at}')"
        )
    sql.append("INSERT INTO support_tickets (ticket_number, employee_id, category, priority, subject, description, status, created_at) VALUES")
    sql.append(",\n".join(ticket_lines))
    sql.append("ON CONFLICT (ticket_number) DO NOTHING;\n")

    # 9. Seed Notifications
    sql.append("-- ─────────────────────────────────────────────────────────────")
    sql.append("-- 9. SEED NOTIFICATIONS (System Alerts, Approvals, Reminders)")
    sql.append("-- ─────────────────────────────────────────────────────────────")
    
    notifs = [
        ("EMP1032", "Leave Application Approved", "Your Earned Leave application for 2026-10-08 to 2026-10-09 has been approved by your manager.", "leave_approved", "leave", "2026-10-01T10:00:00Z", True),
        ("EMP1032", "Attendance Correction Approved", "Your attendance correction request for 2026-10-05 has been approved by HR.", "attendance_correction_approved", "attendance", "2026-10-06T09:30:00Z", True),
        ("EMP1032", "Support Ticket Update", "Ticket #HD-2026-1042 has been assigned to Network Engineering team (Status: In Progress).", "ticket_alert", "hd", "2026-10-26T10:00:00Z", False),
        ("EMP1032", "Timesheet Reminder", "Please remember to submit your timesheet for the current week ending 2026-11-01.", "timesheet_alert", "ts", "2026-10-27T09:00:00Z", False),
        ("EMP1000", "Pending Leave Application", "EMP1032 (Omkar Rao) has submitted a Casual Leave request for 2026-10-30.", "leave_applied", "admin", "2026-10-26T14:30:00Z", False),
        ("EMP1000", "Pending Attendance Correction", "EMP1032 (Omkar Rao) has requested an attendance correction for 2026-10-23.", "attendance_correction", "admin", "2026-10-24T10:00:00Z", False),
        ("EMP1000", "Timesheet Submission", "EMP1032 (Omkar Rao) has submitted timesheet for week 2026-10-19 to 2026-10-25 (24.0h).", "timesheet_approval", "ts", "2026-10-25T18:00:00Z", False),
        ("EMP1032", "Holiday Reminder", "Upcoming Holiday: Balipadyami on Tuesday, 10 November 2026 (Bangalore Location).", "holiday_alert", "leave", "2026-10-27T08:00:00Z", False)
    ]
    
    notif_lines = []
    for eid, title, msg, n_type, act_url, cr_at, is_r in notifs:
        is_r_str = "TRUE" if is_r else "FALSE"
        notif_lines.append(
            f"    ('{eid}', '{title}', '{msg}', '{n_type}', '{act_url}', '{cr_at}', {is_r_str})"
        )
    sql.append("INSERT INTO notifications (employee_id, title, message, type, action_url, created_at, is_read) VALUES")
    sql.append(",\n".join(notif_lines) + ";\n")

    return "\n".join(sql)

def main():
    print("Generating complete October 2026 dataset (Oct 1 - Oct 27)...")
    from generate_org_data import build_250_organization
    emps = build_250_organization()
    print(f"Loaded {len(emps)} active employee profiles.")
    
    sql_content = build_october_sql(emps)
    out_file = os.path.join(os.path.dirname(__file__), "seed_october_2026.sql")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(sql_content)
        
    print(f"[OK] Generated complete October 2026 SQL seed migration: {out_file}")

if __name__ == "__main__":
    main()
