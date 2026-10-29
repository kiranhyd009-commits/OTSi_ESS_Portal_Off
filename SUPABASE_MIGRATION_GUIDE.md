# 🚀 Supabase Database Migration Guide: AWS `ap-south-1`

This guide explains how to migrate all schemas, tables, and 8,000+ data records to your new Supabase project **`OTSi_EmployeeSelfServices`** located in **AWS `ap-south-1` (Mumbai)**.

---

## 📌 Project Details
- **Project Name:** `OTSi_EmployeeSelfServices`
- **Region:** AWS `ap-south-1` (Mumbai)
- **Project ID:** `uccjwsygyzopvcdbmakg`
- **Project URL:** `https://uccjwsygyzopvcdbmakg.supabase.co`

---

## 📦 Migration Files Prepared

Because Supabase Web SQL Editor has a query size limit, the migration has been organized into 4 small, fast SQL files in [`ESS_Backend/migration_parts/`](file:///d:/OTSi_ESS_Portal/ESS_Backend/migration_parts):

| Part | File Name | Description | Size |
|---|---|---|---|
| **Part 1** | [`01_schema_and_core_data.sql`](file:///d:/OTSi_ESS_Portal/ESS_Backend/migration_parts/01_schema_and_core_data.sql) | Creates all 16 tables + indexes + inserts 106 Employees, Leaves, Tickets, Roles | 185 KB |
| **Part 2** | [`02_attendance_logs_part1.sql`](file:///d:/OTSi_ESS_Portal/ESS_Backend/migration_parts/02_attendance_logs_part1.sql) | Attendance logs (Batch 1: ~2,700 records) | 539 KB |
| **Part 3** | [`03_attendance_logs_part2.sql`](file:///d:/OTSi_ESS_Portal/ESS_Backend/migration_parts/03_attendance_logs_part2.sql) | Attendance logs (Batch 2: ~2,700 records) | 534 KB |
| **Part 4** | [`04_notifications_and_audit.sql`](file:///d:/OTSi_ESS_Portal/ESS_Backend/migration_parts/04_notifications_and_audit.sql) | Notifications (2,031) + Audit Logs (779) + Sequence IDs | 621 KB |

---

## ⚡ Step-by-Step Migration via Supabase Web SQL Editor

Open your browser at:
🔗 **[https://supabase.com/dashboard/project/uccjwsygyzopvcdbmakg/sql/new](https://supabase.com/dashboard/project/uccjwsygyzopvcdbmakg/sql/new)**

1. **Run Part 1**:
   - Open [`migration_parts/01_schema_and_core_data.sql`](file:///d:/OTSi_ESS_Portal/ESS_Backend/migration_parts/01_schema_and_core_data.sql)
   - Copy all → Paste into SQL Editor → Click **Run** (green button).

2. **Run Part 2**:
   - Open [`migration_parts/02_attendance_logs_part1.sql`](file:///d:/OTSi_ESS_Portal/ESS_Backend/migration_parts/02_attendance_logs_part1.sql)
   - Copy all → Paste into SQL Editor → Click **Run**.

3. **Run Part 3**:
   - Open [`migration_parts/03_attendance_logs_part2.sql`](file:///d:/OTSi_ESS_Portal/ESS_Backend/migration_parts/03_attendance_logs_part2.sql)
   - Copy all → Paste into SQL Editor → Click **Run**.

4. **Run Part 4**:
   - Open [`migration_parts/04_notifications_and_audit.sql`](file:///d:/OTSi_ESS_Portal/ESS_Backend/migration_parts/04_notifications_and_audit.sql)
   - Copy all → Paste into SQL Editor → Click **Run**.

---

## 🔑 Configure `.env` on Your Laptop

1. In Supabase Dashboard, go to ⚙️ **Project Settings** → **API**.
2. Copy your **`anon` `public`** key (or `service_role` secret key).
3. Update [`ESS_Backend/.env`](file:///d:/OTSi_ESS_Portal/ESS_Backend/.env):

```env
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_APP=app.py
JWT_SECRET_KEY=otsi-ess-local-admin-bootstrap-2026

SUPABASE_URL=https://uccjwsygyzopvcdbmakg.supabase.co
SUPABASE_KEY=<PASTE_YOUR_NEW_API_KEY_HERE>

CORS_ORIGINS=http://localhost:3000,http://localhost:5000,http://127.0.0.1:5000
SERVER_PORT=5000
SERVER_HOST=0.0.0.0
MFA_ENABLED=false
```

---

## 🚀 Running the Web Application

1. Double-click **[`start_server.bat`](file:///d:/OTSi_ESS_Portal/start_server.bat)**.
2. Open **[`otsi-attendance-portal.html`](file:///d:/OTSi_ESS_Portal/otsi-attendance-portal.html)** in your browser or go to `http://127.0.0.1:5000`.

### Login Credentials:
| Role | Email | Password |
|---|---|---|
| **Super Admin** | `admin.otsi@otsi-usa.com` | `R@vikiran332!` |
| **Admin / Leadership** | `kiran.us009@gmail.com` | `R@vikiran332` |
| **Employee** | `ravi.mallem@otsi.co.in` | `R@vikiran332` |
