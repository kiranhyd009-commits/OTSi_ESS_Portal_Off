# OTSi ESS Portal — Comprehensive Application Functionality Audit & System Analysis

**Date:** September 1, 2026  
**Application:** OTSi Attendance & Employee Self-Service (ESS) Portal  
**Backend:** Flask API (Python) connected to Supabase PostgreSQL  
**Frontend:** Single Page Application (HTML5 / Vanilla JS / CSS3)  
**Status:** Live on `http://127.0.0.1:5000`

---

## 1. Executive Summary

We conducted a complete, end-to-end architectural and functional review of the OTSi ESS Portal. Every major module—including user role scoping (Employee, Manager, HR Manager, System Administrator), attendance lifecycle, leave management, corrections, profile updates, IT helpdesk tickets, security authentication flows, and notification mechanisms—was examined across backend routes and frontend UI bindings.

The application is structured cleanly, with well-defined database schemas and role-based access controls. Below is the detailed breakdown of the working status, identified observations, and recommended enhancements.

---

## 2. Module-by-Module Functionality Review

### 2.1. Authentication & Security (MFA, Password Resets, Logins)
- **Login Flow (`/api/auth/login`):**
  - Works for both Employee ID (`EMP####`, `OTSI####`, `ADMIN####`) and Work Email (`@otsi-usa.com`, `@otsi.co.in`).
  - **Account Lockout:** 5 failed attempts trigger a 15-minute temporary lockout.
  - **90-Day Password Expiry:** Handled with a temporary JWT token prompting the user to update their password.
- **MFA Flow (`/api/auth/mfa-verify`, `/api/auth/mfa-toggle`):**
  - Application-wide feature flag correctly accounts for dummy email environments.
  - Generates 6-digit OTP stored in database with a 5-minute expiry, displayed in console and notifications.
  - Admin MFA toggle is protected at the application configuration level.
- **Forgot Password & Password Reset (`/api/auth/forgot-password`, `/api/auth/reset-password`):**
  - Validates OTSi email domain and format.
  - Sends password reset email asynchronously with JWT token and logs the mock link directly to the console for local debugging.
  - Validates strict password policy (min 8 chars, uppercase, lowercase, numbers, special characters) and prevents password reuse against `password_history`.
- **Internal Password Change (`/api/auth/change-password`):**
  - Validates old password, policy checks, password history, and updates `password_changed_at`.

---

### 2.2. Attendance Management & Geofencing Location Detection
- **Check-in (`/api/attendance/check-in`):**
  - **Office Mode:** Uses the Haversine formula against OTSi Office GPS coordinates (`17.4474, 78.3762`) with configurable radius (e.g. 500m). Rejects out-of-bounds check-ins with `403 Geofence error`.
  - **WFH Mode:** Bypasses geofence check when WFH toggle is enabled.
  - **Late Detection:** Accurately converts UTC timestamp to **IST (+05:30)** and marks status as `late` if check-in occurs after 09:30 AM IST.
- **Check-out (`/api/attendance/check-out`):**
  - Calculates total working hours; automatically flags `< 7.0` hours as `half_day`.
  - Dispatches IST-formatted check-out notification to employee.
- **Attendance Statistics & History (`/api/attendance/stats`, `/api/attendance/history`):**
  - Computes monthly Present, WFH, Half Day, On Leave, Corrections, and Total Hours.
  - Features intelligent weekday gap-filling (skipping weekends and official holidays) to compute actual absences.
- **Attendance Corrections (`/api/attendance/correction/request`, `/api/attendance/correction/history`):**
  - Employees can submit check-in/check-out timestamp corrections with a mandatory reason.
  - Validates against future times and ensures check-out is after check-in.
  - HR/Managers receive instant notifications with direct deep-links.

---

### 2.3. Leave Management & Balance Deduction Engine
- **Leave Application (`/api/leave/apply`):**
  - Supports multiple leave types: `Casual & Sick (CSL)`, `Earned (EL)`, `Bereavement`, `Marriage`, `LOP`, `WFH`, `Permission`, `Paternity`, `Optional Holiday`.
  - Automatic exclusion of weekends and official public holidays from calculated leave day count.
  - **Client-Side Balance Check:** Notifies user when requested days exceed remaining balance, alerting them that LOP (Loss of Pay) will be applied upon approval.
  - Dispatches notifications to assigned Manager and all HR/Admin personnel.
- **Leave Approval & Deduction Flow (`/api/admin/approve-leave/<id>`, `/api/admin/reject-leave/<id>`):**
  - **Cascading Deduction Logic (`LeaveUtils.deduct_leave`):**
    - `Casual/Sick Leave`: Deducts from `casual_leave` $\rightarrow$ `sick_leave` $\rightarrow$ overflows excess into `lop_leave`.
    - `Earned Leave`: Deducts from `earned_leave` $\rightarrow$ `casual_leave` $\rightarrow$ `sick_leave` $\rightarrow$ `lop_leave`.
    - Non-balance types (`WFH`, `Permission`, `Paternity`, `Optional Holiday`) are recorded without numeric deduction.
- **Cancel Leave (`/api/leave/cancel/<id>`):**
  - Allows employees to self-cancel `pending` leave applications before reviewer action.
- **Company Holidays (`/api/holidays`):**
  - Dynamic India & US holiday lists with region toggle and client-side PDF export using `jsPDF`.
- **Leave Module UI Layout Guidelines:**
  - **Header Banner:** Gradient background with user greeting and prominent *"+ Apply Leave"* action button.
  - **Top Row (Two Columns):**
    - *Left Stack (`.leave-main-stack`):* 5 compact stat cards for Leave Balances (`CSL`, `EL`, `Marriage`, `Bereavement`, `LOP`) + 4-column compact metric box for Permission Summary (`Early Logout`, `Late Login`, `2hrs Permission`, `WFH Status`).
    - *Right Column (`.leave-quick-nav-top`):* Slim ($210\text{px}$) Quick Navigation card with interactive pills (`Leave Status`, `Work From Home`, `Cancel Leave`, `Company Holidays`).
  - **Bottom Views (100% Full Width):** Notification banner callout and full-width responsive tabular views for Application History, Cancel Pending, WFH Status, and Holidays Calendar.
  - **Mobile Responsive:** Fluid single/double column stacking for mobile ($<640\text{px}$) and tablet ($<1024\text{px}$) screens.

---

### 2.4. Employee Profiles, New Joinee Requests & Profile Corrections
- **Profile View (`/api/profile`):**
  - Returns sanitized employee details, manager status (`is_manager`), system admin flag, assigned HRBP, and MFA configuration status.
- **Profile Update Requests (`/api/profile/update-requests`):**
  - Changes to name, phone, department, team, designation, or manager require HR approval.
  - Special bypass rule for master administrative accounts.
- **New Joinee Registrations & Admin Approval (`/api/auth/register`, `/api/admin/employees/<id>/status`):**
  - Self-registered employees enter as `inactive` (pending review).
  - Admin/HR dashboard displays a dedicated **Pending Registrations** queue with 1-click **Approve** (activate) or **Reject** (purge/deactivate).

---

### 2.5. IT Help Desk & Support Tickets
- **Ticket Creation (`/api/tickets/create`):**
  - Generates standard reference IDs (e.g., `HD-2026-####`) across categories: Hardware, Software, Network, Access/Permissions, Email/Account.
  - Priority levels: P1 (High), P2 (Medium), P3 (Minor).
- **Ticket Management (`/api/tickets`, `/api/admin/tickets`, `/api/admin/tickets/<id>/update`):**
  - Employees see only their submitted tickets.
  - Admin/SNA support staff see all tickets and can post threaded response updates and status transitions (`open` $\rightarrow$ `in_progress` $\rightarrow$ `resolved` $\rightarrow$ `closed`).
  - Automatic notification dispatched to employee upon status or comment update.

---

### 2.6. Multi-Role Scoping (Employee vs Manager vs HR vs Admin)

| Capability / Module | Employee | Manager (Reporting Lead) | HR Manager | System Admin (`OTSI0001`) |
| :--- | :---: | :---: | :---: | :---: |
| **Attendance Check-in / History** | Self Only | Self + Team Today View | Self + Full Org Logs | Full Org Logs & CSV Export |
| **Attendance Corrections** | Submit / History | Approve Direct Reportees | Approve All | Approve All |
| **Leave Management** | Apply / Cancel | Approve Direct Reportees | Approve All Org Leaves | Full Access |
| **Timesheets** | Create / Edit / Submit | View / Approve Reportees | Org Overview | Full Access |
| **Profile & Corrections** | Submit Edit Request | View Reportee Profiles | Approve Edit Requests | Full Edit & Status Management |
| **New Joinee Registrations** | — | — | Review & Approve | Review & Approve |
| **Support Tickets** | My Tickets | My Tickets | My Tickets | Global Queue & Resolution |
| **Org Structure & Analytics** | My Team Context | Direct Reports Stats | Full Dept/Team Breakdown | Full Dept/Team Breakdown |

---

## 3. Real-time Notifications & UI Deep-Linking
- **In-App Notification Bell (`/api/notifications`):**
  - Actionable notification payloads contain `action_url` metadata (e.g., `leave_approval:<id>`, `attendance_correction:<id>`, `hd`, `ts`).
  - Clicking a notification navigates directly to the relevant sub-view and flashes/highlights the specific pending card for fast review.
  - Polling interval set to 30 seconds with automatic unread badge counter.

---

## 4. Key Observations & Potential Opportunities for Discussion

During our analysis, we noted several high-value ideas we can discuss before implementing any enhancements:

1. **Manager Multi-Level Approval Hierarchy:**
   - *Current state:* Single-stage approval (either Direct Manager or HR can approve).
   - *Idea:* Optional dual-level approval where leave/correction requests first go to the Reporting Manager, and once approved, proceed to HR for final sign-off.

2. **Shift Schedules & Flexible Working Hours:**
   - *Current state:* Fixed office start time of 09:30 AM IST.
   - *Idea:* Introduce configurable shifts (e.g., General: 9:30 AM – 6:30 PM, US Shift: 6:30 PM – 3:30 AM, Flexible: 9-hour window).

3. **Timesheet Manager Approval Action UI:**
   - *Current state:* Timesheets can be drafted, filled, and submitted by employees.
   - *Idea:* Provide a dedicated "Timesheet Approvals" tab in the Manager/HR dashboard matching the Leave & Correction review UI.

4. **Monthly Leave Accrual Automation:**
   - *Current state:* Leave balances are set during registration and updated on approved applications.
   - *Idea:* Add a scheduled monthly credit background job (e.g., +1.75 days Earned Leave, +1.0 day Casual/Sick leave at the start of each month).

5. **Notification Push & Webhook Integration:**
   - *Current state:* In-app notification bell + console/SMTP email dispatch.
   - *Idea:* Optional Microsoft Teams / Slack webhook notifications for instant approval alerts to managers.

---

## 5. Conclusion & Next Steps

The OTSi ESS Portal is functioning reliably with solid business logic for geofencing, cascading leave deductions, role isolation, ticket handling, and security policies.

Please review this analysis. Let me know which features, workflows, or new ideas you'd like to refine or modify next!
