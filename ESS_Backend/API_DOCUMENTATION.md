# OTSI Attendance Portal - API Documentation

Complete API reference for the OTSI Attendance Portal backend.

## Base URL

```
Development:  http://localhost:5000
Production:   https://api.yourdomain.com
```

## Authentication

All endpoints (except `/api/health`, `/api/auth/register`, `/api/auth/login`) require a Bearer token:

```
Authorization: Bearer <access_token>
```

## Response Format

### Success Response (2xx)
```json
{
  "message": "Operation successful",
  "data": {},
  "timestamp": "2026-06-11T10:30:00Z"
}
```

### Error Response (4xx, 5xx)
```json
{
  "error": "Error message description",
  "code": "ERROR_CODE",
  "timestamp": "2026-06-11T10:30:00Z"
}
```

---

## 📋 Health Check

### Check API Status
```
GET /api/health
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "timestamp": "2026-06-11T10:30:00Z",
  "service": "OTSI Attendance Portal API"
}
```

---

## 🔐 Authentication

### Register New Employee

```
POST /api/auth/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "employee_id": "EMP5834",
  "email": "john@otsi-global.com",
  "full_name": "John Doe",
  "password": "SecurePassword123!"
}
```

**Response (201 Created):**
```json
{
  "message": "Registration successful. Please sign in.",
  "employee_id": "EMP5834"
}
```

**Errors:**
- `400` - Missing required fields or invalid email domain
- `400` - Employee ID or email already registered
- `500` - Registration failed

---

### Login

```
POST /api/auth/login
Content-Type: application/json
```

**Request Body:**
```json
{
  "identifier": "EMP5834",
  "password": "SecurePassword123!",
  "role": "employee"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "employee": {
    "employee_id": "EMP5834",
    "email": "john@otsi-global.com",
    "full_name": "John Doe",
    "role": "employee",
    "designation": "Software Engineer"
  }
}
```

**Errors:**
- `400` - Missing credentials
- `401` - Invalid credentials
- `403` - Role mismatch

---

### Logout

```
POST /api/auth/logout
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Logout successful"
}
```

---

### Refresh Token

```
POST /api/auth/refresh
Content-Type: application/json
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

## 📍 Attendance

### Check In

```
POST /api/attendance/check-in
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "latitude": 17.4474,
  "longitude": 78.3762,
  "is_wfh": false
}
```

**Response (200 OK):**
```json
{
  "message": "Checked in successfully",
  "check_in_time": "2026-06-11T09:15:30Z",
  "status": "present",
  "location_verified": true
}
```

**Errors:**
- `400` - Already checked in today or location not allowed
- `401` - Not authenticated

---

### Check Out

```
POST /api/attendance/check-out
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Checked out successfully",
  "check_out_time": "2026-06-11T18:30:00Z",
  "working_hours": 9.25
}
```

---

### Get Today's Attendance

```
GET /api/attendance/today
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 123,
  "status": "present",
  "check_in_time": "2026-06-11T09:15:30Z",
  "check_out_time": "2026-06-11T18:30:00Z",
  "working_hours": 9.25,
  "is_wfh": false,
  "is_late": false
}
```

---

### Get Attendance History

```
GET /api/attendance/history?days=30
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `days` (optional, default=30) - Number of days of history

**Response (200 OK):**
```json
{
  "attendance_logs": [
    {
      "id": 123,
      "employee_id": "EMP5834",
      "attendance_date": "2026-06-11",
      "check_in_time": "2026-06-11T09:15:30Z",
      "check_out_time": "2026-06-11T18:30:00Z",
      "working_hours": 9.25,
      "status": "present",
      "is_wfh": false,
      "is_late": false
    }
  ],
  "count": 20
}
```

---

### Get Attendance Statistics

```
GET /api/attendance/stats?month=6&year=2026
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `month` (optional) - Month number (1-12)
- `year` (optional) - Year

**Response (200 OK):**
```json
{
  "present": 18,
  "absent": 2,
  "late": 3,
  "wfh": 5,
  "half_day": 0,
  "total_hours": 175.5
}
```

---

## 🗓️ Leave Management

### Get Leave Balance

```
GET /api/leave/balance
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "casual_leave": 11,
  "sick_leave": 8,
  "earned_leave": 10.5,
  "bereavement_leave": 3,
  "marriage_leave": 0,
  "lop_leave": 0
}
```

---

### Apply for Leave

```
POST /api/leave/apply
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "leave_type": "casual",
  "start_date": "2026-06-15",
  "end_date": "2026-06-17",
  "reason": "Personal work"
}
```

**Response (201 Created):**
```json
{
  "message": "Leave application submitted",
  "application_id": 456
}
```

**Errors:**
- `400` - Invalid leave type or insufficient balance
- `401` - Not authenticated

---

### Get Leave History

```
GET /api/leave/history
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "leave_applications": [
    {
      "id": 456,
      "employee_id": "EMP5834",
      "leave_type": "casual",
      "start_date": "2026-06-15",
      "end_date": "2026-06-17",
      "number_of_days": 3,
      "reason": "Personal work",
      "status": "pending",
      "created_at": "2026-06-11T10:00:00Z"
    }
  ]
}
```

---

## 📊 Timesheet

### Create Timesheet

```
POST /api/timesheet/create
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "week_start_date": "2026-06-08",
  "week_end_date": "2026-06-12"
}
```

**Response (201 Created):**
```json
{
  "message": "Timesheet created",
  "timesheet_id": 789
}
```

---

### Add Timesheet Entry

```
POST /api/timesheet/789/add-entry
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "entry_date": "2026-06-08",
  "project_name": "Phoenix API",
  "task_description": "Feature Development",
  "hours_worked": 8.5
}
```

**Response (201 Created):**
```json
{
  "message": "Entry added",
  "entry_id": 1001
}
```

---

### Submit Timesheet

```
POST /api/timesheet/789/submit
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Timesheet submitted"
}
```

---

## 🎫 Support Tickets

### Create Support Ticket

```
POST /api/tickets/create
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "category": "Hardware Issue",
  "priority": "p2",
  "subject": "Monitor not working",
  "description": "External monitor stopped working after power outage"
}
```

**Response (201 Created):**
```json
{
  "message": "Ticket created",
  "ticket_number": "HD-2026-5832"
}
```

---

### Get Support Tickets

```
GET /api/tickets
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "tickets": [
    {
      "id": 1,
      "ticket_number": "HD-2026-5832",
      "employee_id": "EMP5834",
      "category": "Hardware Issue",
      "priority": "p2",
      "subject": "Monitor not working",
      "description": "External monitor stopped working after power outage",
      "status": "open",
      "created_at": "2026-06-11T14:20:00Z"
    }
  ],
  "count": 5
}
```

---

## 👤 Employee Profile

### Get Profile

```
GET /api/profile
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "employee_id": "EMP5834",
  "email": "john@otsi-global.com",
  "full_name": "John Doe",
  "designation": "Software Engineer",
  "department": "Engineering",
  "manager_id": "EMP4001",
  "manager_name": "Kiran Mullapudi",
  "phone": "+91-9876543210",
  "role": "employee",
  "status": "active",
  "date_of_joining": "2023-01-15"
}
```

---

### Update Profile

```
PUT /api/profile/update
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "phone": "+91-9876543210",
  "designation": "Senior Software Engineer"
}
```

**Response (200 OK):**
```json
{
  "message": "Profile updated"
}
```

---

## 👥 HR/Admin Endpoints

### Get All Employees (HR/Admin only)

```
GET /api/admin/employees
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "employees": [
    {
      "employee_id": "EMP5834",
      "email": "john@otsi-global.com",
      "full_name": "John Doe",
      "designation": "Software Engineer",
      "role": "employee",
      "status": "active"
    }
  ],
  "count": 50
}
```

---

### Get Team Attendance (HR/Admin only)

```
GET /api/admin/team-attendance
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "team_attendance": [
    {
      "employee_id": "EMP5834",
      "name": "John Doe",
      "designation": "Software Engineer",
      "status": "present",
      "check_in_time": "2026-06-11T09:15:30Z",
      "is_wfh": false
    }
  ],
  "count": 45
}
```

---

### Get Leave Approvals (HR/Admin only)

```
GET /api/admin/leave-approvals
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "leave_applications": [
    {
      "id": 456,
      "employee_id": "EMP5834",
      "leave_type": "casual",
      "start_date": "2026-06-15",
      "end_date": "2026-06-17",
      "number_of_days": 3,
      "reason": "Personal work",
      "status": "pending",
      "created_at": "2026-06-11T10:00:00Z"
    }
  ],
  "count": 12
}
```

---

### Approve Leave (HR/Admin only)

```
POST /api/admin/approve-leave/456
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "comments": "Approved"
}
```

**Response (200 OK):**
```json
{
  "message": "Leave approved"
}
```

---

### Reject Leave (HR/Admin only)

```
POST /api/admin/reject-leave/456
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "comments": "Insufficient documentation"
}
```

**Response (200 OK):**
```json
{
  "message": "Leave rejected"
}
```

---

### Get Dashboard Statistics (HR/Admin only)

```
GET /api/admin/dashboard-stats
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "total_employees": 50,
  "present_today": 42,
  "wfh_today": 5,
  "absent_today": 3,
  "pending_leaves": 8,
  "open_tickets": 12
}
```

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| 400 | Bad Request | Missing or invalid parameters |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions for this action |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 500 | Server Error | Internal server error |

---

## Rate Limiting

- Default: 1000 requests per hour per IP
- Authentication endpoints: 10 requests per minute

---

## Testing with cURL

### Test API Health
```bash
curl -X GET http://localhost:5000/api/health
```

### Register Employee
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "EMP5835",
    "email": "jane@otsi-global.com",
    "full_name": "Jane Smith",
    "password": "SecurePass123!"
  }'
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "EMP5835",
    "password": "SecurePass123!",
    "role": "employee"
  }'
```

### Check In (replace TOKEN with actual access_token)
```bash
curl -X POST http://localhost:5000/api/attendance/check-in \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "latitude": 17.4474,
    "longitude": 78.3762,
    "is_wfh": false
  }'
```

---

## Webhooks (Future)

- Employee check-in
- Leave approval/rejection
- Ticket status changes
- Timesheet submission

---

Last Updated: 2026-06-11
