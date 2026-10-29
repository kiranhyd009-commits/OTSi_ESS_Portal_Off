# Project Architecture & Data Flow

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER (Browser)                     │
│                   otsi-attendance-portal.html                   │
│  (HTML, CSS, JavaScript - Frontend UI)                         │
│                                                                 │
│  [Login] → [Attendance] → [Leave] → [Timesheet] → [Support]   │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST (JSON)
                             │ Port 5000
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    API LAYER (Flask Backend)                    │
│             d:\OTSi_ESS_Portal\ESS_Backend\app.py               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 30+ API Endpoints                                       │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ • Authentication (login, register, logout)             │  │
│  │ • Attendance (check-in, check-out, history, stats)    │  │
│  │ • Leave (balance, apply, history, approvals)          │  │
│  │ • Timesheet (create, add entry, submit)               │  │
│  │ • Tickets (create, list, track)                       │  │
│  │ • Admin (employee list, team view, approvals)         │  │
│  │ • Profile (get, update)                               │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Security Layer:                                               │
│  • JWT Authentication & Authorization                         │
│  • Password Hashing (bcrypt)                                 │
│  • Input Validation                                           │
│  • CORS Configuration                                         │
│  • Audit Logging                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │ Supabase SDK
                             │ PostgreSQL Driver
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                  DATABASE LAYER (Supabase)                      │
│                   PostgreSQL Database                           │
│                   https://supabase.com                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Employees   │  │ Attendance   │  │  Leave       │         │
│  │  Table       │  │  Logs Table  │  │  Tables      │         │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤         │
│  │ • ID         │  │ • EmpID      │  │ • Balance    │         │
│  │ • Email      │  │ • Date       │  │ • Apps       │         │
│  │ • Password   │  │ • Check-in   │  │ • History    │         │
│  │ • Role       │  │ • Check-out  │  │ • Approvals  │         │
│  │ • Details    │  │ • Hours      │  │ • Deductions │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Timesheets   │  │ Support      │  │ Notifications│         │
│  │ & Entries    │  │ Tickets      │  │ & Audit Logs │         │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤         │
│  │ • Weekly     │  │ • ID         │  │ • Notifications      │
│  │ • Projects   │  │ • Category   │  │ • Audit Trail        │
│  │ • Tasks      │  │ • Priority   │  │ • Activity Logs      │
│  │ • Hours      │  │ • Status     │  │                       │
│  │ • Approval   │  │ • Resolution │  │                       │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Diagrams

### 1. Login Flow
```
Frontend                Backend              Database
   │                      │                      │
   ├─ Login Request ─────→│                      │
   │  (ID, Password,      │                      │
   │   Role)              │                      │
   │                      ├─ Query Employee ────→│
   │                      │                      ├─ Find by ID/Email
   │                      │←─ Employee Record ───┤
   │                      │                      │
   │                      ├─ Verify Password     │
   │                      │  (bcrypt compare)    │
   │                      │                      │
   │                      ├─ Generate JWT Token  │
   │                      │  (HS256)             │
   │                      │                      ├─ Update Last Login
   │←─ Access Token ──────┤                      │
   │   Refresh Token      │                      │
   │   User Data          │                      │
   │                      │←─ Success ───────────┤
   │                      │                      │
   ├─ Store Token (LocalStorage)
   │
   ├─ Redirect to Dashboard
   │
   └─ Include Token in Future Requests
      Authorization: Bearer [TOKEN]
```

### 2. Check-In Flow
```
Frontend                Backend              Database
   │                      │                      │
   ├─ Get Location ───────│                      │
   │  (from browser)      │                      │
   │                      │                      │
   ├─ Check-In Request ──→│                      │
   │  (Latitude,          │                      │
   │   Longitude,         │                      │
   │   WFH Mode)          │                      │
   │                      ├─ Verify Auth Token   │
   │                      │                      │
   │                      ├─ Calculate Distance  │
   │                      │  (Haversine formula) │
   │                      │  Verify Location     │
   │                      │                      │
   │                      ├─ Check if Late       │
   │                      │  (current time       │
   │                      │   vs 9:00 AM)        │
   │                      │                      ├─ Insert Attendance Record
   │                      │                      │  (Date, Time, Status, etc)
   │←─ Success ───────────┤                      │
   │  (Check-in Time,     │←─ Record Saved ─────┤
   │   Status,            │
   │   Location           │
   │   Verified)          │                      ├─ Create Notification
   │                      │                      │
   ├─ Update UI           │                      │
   │  • Show check-in time│                      │
   │  • Show working hours│                      │
   │  • Enable check-out  │                      │
   │                      │                      │
   └─ Display Success Toast
```

### 3. Leave Application Flow
```
Frontend                Backend              Database
   │                      │                      │
   ├─ Apply Leave ───────→│                      │
   │  (Type, Dates,       │                      │
   │   Reason)            │                      │
   │                      ├─ Verify Auth Token   │
   │                      │                      │
   │                      ├─ Calculate Days      │
   │                      │  (excluding weekends)│
   │                      │                      ├─ Check Leave Balance
   │                      │                      │←─ Current Balance
   │                      │                      │
   │                      ├─ Validate Balance    │
   │                      │  (enough leave?)     │
   │                      │                      ├─ Create Leave Application
   │                      │                      │  (Status: Pending)
   │←─ Success ───────────┤                      │
   │  (Application ID)    │←─ Record Saved ─────┤
   │                      │                      │
   │                      │                      ├─ Notify HR Manager
   │                      │                      │  (New Leave to Approve)
   │                      │                      │
   ├─ Display Confirmation│                      │
   │                      │                      │
   └─ Show in Leave History
        (Status: Pending)
```

### 4. HR Approval Flow
```
HR Manager               Backend              Database
   │                      │                      │
   ├─ View Pending ──────→│                      │
   │  Leaves              │                      │
   │                      ├─ Query Pending ────→│
   │←─ Pending List ──────┤  Applications       │
   │  (with details)      │←─ List Returned ────┤
   │                      │                      │
   ├─ Approve Leave ─────→│                      │
   │  (App ID,            │                      │
   │   Comments)          │                      ├─ Update Leave Application
   │                      │                      │  (Status: Approved)
   │                      │                      │  (Set Approval Date/By)
   │                      │                      │
   │                      │                      ├─ Update Leave Balance
   │                      │                      │  (Deduct from total)
   │←─ Success ───────────┤                      │
   │                      │←─ All Updates Done ─┤
   │                      │                      │
   │                      │                      ├─ Notify Employee
   │                      │                      │  (Leave Approved)
   │                      │                      │
   └─ Refresh List
        (Application removed from pending)
```

---

## 🔄 Request/Response Cycle

```
FRONTEND (Browser)
    │
    └─ User Action
       (Login, Check-in, Apply Leave, etc)
       │
       └─ JavaScript Event Handler
          │
          └─ Prepare JSON Request
             │
             └─ Add Headers:
                • Content-Type: application/json
                • Authorization: Bearer [TOKEN]
                │
                └─ Send HTTP Request
                   (POST/GET/PUT to localhost:5000)
                   │
                   ↓
BACKEND (Flask)
    │
    ├─ Receive Request
    │
    ├─ Parse JSON Body
    │
    ├─ Validate Headers
    │  ├─ Check Authorization Token
    │  ├─ Verify JWT Signature
    │  └─ Extract User Info
    │
    ├─ Validate Input
    │  ├─ Check Required Fields
    │  ├─ Validate Data Types
    │  └─ Check Business Rules
    │
    ├─ Call Database
    │  ├─ Query/Insert/Update/Delete
    │  └─ Handle Transactions
    │
    ├─ Process Business Logic
    │  ├─ Calculations
    │  ├─ Validations
    │  └─ Notifications
    │
    ├─ Prepare JSON Response
    │  ├─ Success: Data + Status 200
    │  └─ Error: Error Message + Status Code
    │
    └─ Send Response
       │
       ↓
FRONTEND (Browser)
    │
    ├─ Receive Response
    │
    ├─ Check Status Code
    │
    ├─ Parse JSON Response
    │
    ├─ Update UI
    │  ├─ Update DOM elements
    │  ├─ Show messages/toasts
    │  └─ Refresh lists/data
    │
    └─ Display to User
```

---

## 📱 Component Interaction

```
┌─────────────────────────────────────────────────────┐
│              Frontend (HTML/JS/CSS)                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ Auth Screen (Login/Register)                │  │
│  └────────────┬─────────────────────────────────┘  │
│               │ (after login)                      │
│  ┌────────────▼─────────────────────────────────┐  │
│  │         Main App Shell                       │  │
│  ├──────────────────────────────────────────────┤  │
│  │ • Header (Logo, Avatar, Notifications)      │  │
│  │ • Bottom Navigation (5 main tabs)           │  │
│  │ • Pages (Hidden/Shown based on nav)         │  │
│  │                                              │  │
│  │ ┌──────────────────────────────────────────┐│  │
│  │ │ Page 1: Attendance                       ││  │
│  │ │ [Check-in] [Check-out] [History] [Stats]││  │
│  │ └──────────────────────────────────────────┘│  │
│  │ ┌──────────────────────────────────────────┐│  │
│  │ │ Page 2: Leave                            ││  │
│  │ │ [Balance] [Apply] [History] [Status]    ││  │
│  │ └──────────────────────────────────────────┘│  │
│  │ ┌──────────────────────────────────────────┐│  │
│  │ │ Page 3: Timesheet                        ││  │
│  │ │ [Create] [Add Entries] [Submit]         ││  │
│  │ └──────────────────────────────────────────┘│  │
│  │ ┌──────────────────────────────────────────┐│  │
│  │ │ Page 4: Help Desk                        ││  │
│  │ │ [Create Ticket] [View Tickets] [Status]  ││  │
│  │ └──────────────────────────────────────────┘│  │
│  │ ┌──────────────────────────────────────────┐│  │
│  │ │ Page 5: Profile                          ││  │
│  │ │ [View Info] [Edit] [Logout]             ││  │
│  │ └──────────────────────────────────────────┘│  │
│  │                                              │  │
│  │ (Additional: HR/Admin Dashboard if role)   │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
         │
         │ HTTP Requests (API Calls)
         ↓
┌─────────────────────────────────────────────────────┐
│          Backend (Flask + Python)                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ Middleware Layer                             │  │
│  │ • CORS Handler                              │  │
│  │ • Request Parser                            │  │
│  │ • Error Handler                             │  │
│  └──────────────────────────────────────────────┘  │
│                │                                   │
│  ┌─────────────▼──────────────────────────────┐  │
│  │ Authentication Layer                        │  │
│  │ • Token Verification (JWT)                 │  │
│  │ • Password Hashing                         │  │
│  │ • Role Verification                        │  │
│  └──────────────────────────────────────────────┘  │
│                │                                   │
│  ┌─────────────▼──────────────────────────────┐  │
│  │ API Endpoints (30+)                         │  │
│  │ • /api/auth/*                              │  │
│  │ • /api/attendance/*                        │  │
│  │ • /api/leave/*                             │  │
│  │ • /api/timesheet/*                         │  │
│  │ • /api/tickets/*                           │  │
│  │ • /api/admin/*                             │  │
│  └──────────────────────────────────────────────┘  │
│                │                                   │
│  ┌─────────────▼──────────────────────────────┐  │
│  │ Business Logic Layer                        │  │
│  │ • Attendance Utils (geolocation, status)   │  │
│  │ • Leave Utils (balance, deduction)         │  │
│  │ • Timesheet Utils (hours calculation)      │  │
│  │ • Notification Utils                       │  │
│  │ • Audit Logging                            │  │
│  └──────────────────────────────────────────────┘  │
│                │                                   │
│  ┌─────────────▼──────────────────────────────┐  │
│  │ Database Layer                              │  │
│  │ • Supabase Client                          │  │
│  │ • Connection Management                    │  │
│  │ • Query Builder                            │  │
│  │ • Transaction Handler                      │  │
│  └──────────────────────────────────────────────┘  │
│                │                                   │
└─────────────────────────────────────────────────────┘
         │
         │ PostgreSQL Queries
         ↓
┌─────────────────────────────────────────────────────┐
│    Supabase / PostgreSQL Database (Cloud)          │
├─────────────────────────────────────────────────────┤
│ • 9 Tables (Employees, Attendance, Leave, etc)    │
│ • Indexes (Performance)                           │
│ • Row-Level Security (Privacy)                    │
│ • Automated Backups                               │
│ • Audit Trail                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🔐 Security Flow

```
REQUEST → Authentication → Authorization → Validation → Processing → RESPONSE

1. Authentication (WHO are you?)
   • Client sends token in Authorization header
   • Backend verifies JWT signature
   • Extracts employee_id and role from token
   • Checks if token is expired
   • If invalid → Return 401 Unauthorized

2. Authorization (Are you ALLOWED?)
   • Check if user's role has permission
   • Employee: Can only see own data
   • HR: Can approve leaves, view team
   • Admin: Full system access
   • If denied → Return 403 Forbidden

3. Validation (Is the DATA valid?)
   • Check required fields present
   • Validate data types
   • Check business rules
   • Example: Leave days < remaining balance?
   • If invalid → Return 400 Bad Request

4. Processing (DO the action)
   • Execute business logic
   • Update database
   • Create notifications
   • Log audit trail

5. Response
   • Success: Return data + 200 OK
   • Error: Return error message + error code
```

---

## ⚡ Performance Optimization

```
Database Optimization:
├─ Indexes on:
│  ├─ Foreign keys
│  ├─ Frequently queried fields
│  ├─ Employee ID + Date (attendance)
│  └─ Employee ID (all tables)
│
├─ Connection Pooling:
│  └─ Managed by Supabase
│
└─ Query Optimization:
   └─ Select only needed columns

API Optimization:
├─ Response Caching (future)
├─ Pagination for large lists
├─ Batch operations
└─ Connection reuse

Frontend Optimization:
├─ LocalStorage for tokens
├─ DOM manipulation efficiency
├─ Event delegation
└─ Lazy loading (future)
```

---

**Last Updated:** 2026-06-11
