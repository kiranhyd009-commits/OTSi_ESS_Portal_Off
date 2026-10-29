# OTSI Attendance Portal - Backend API

A full-fledged Python backend for employee attendance tracking, leave management, timesheet submissions, and IT support ticketing system. Built with Flask and Supabase.

## Features

✅ **Authentication & Authorization**
- Employee registration and login
- Role-based access control (Employee, HR, Admin)
- JWT token-based authentication
- Refresh token support

✅ **Attendance Management**
- Check-in/check-out with geolocation verification
- WFH (Work From Home) mode support
- Automatic late detection
- Working hours calculation
- Attendance history and statistics

✅ **Leave Management**
- Apply for different types of leave (Casual, Sick, Earned, etc.)
- Leave balance tracking
- Leave approval workflow
- Leave history

✅ **Timesheet Management**
- Weekly timesheet creation
- Project and task tracking
- Hours per entry
- Timesheet submission and approval

✅ **IT Support Ticketing**
- Create support tickets with priority levels
- Ticket tracking and status updates
- Category-based organization

✅ **HR Dashboard**
- Real-time team attendance view
- Employee statistics
- Leave approval management
- System-wide analytics

✅ **Audit & Notifications**
- Complete audit trail for all actions
- Real-time notifications
- Activity logging

## Technology Stack

- **Backend**: Flask 2.3.3 (Python)
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT (Flask-JWT-Extended)
- **CORS**: Flask-CORS
- **Password Hashing**: Werkzeug
- **Server**: Gunicorn

## Prerequisites

- Python 3.8+
- Supabase account (https://supabase.com)
- Git
- Virtual environment (venv/conda)

## Installation

### 1. Clone/Setup Project

```bash
cd "d:\OTSi_ESS_Portal\ESS_Backend"
```

### 2. Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Supabase

#### a. Create Supabase Project
1. Go to https://supabase.com
2. Sign in or create account
3. Create a new project
4. Copy your Project URL and API Key

#### b. Initialize Database Schema
1. Go to Supabase SQL Editor
2. Create a new query
3. Copy content from `database_schema.sql`
4. Execute the query
5. This will create all tables and indexes

### 5. Configure Environment Variables

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your values
```

Edit `.env` file:

```env
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_APP=app.py

# JWT Secret (Generate a random string)
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-api-key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5000,https://yourdomain.com

# Server
SERVER_PORT=5000
SERVER_HOST=0.0.0.0
```

### 6. Run Application

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Health Check
- `GET /api/health` - Check API status

### Authentication
- `POST /api/auth/register` - Register new employee
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `POST /api/auth/refresh` - Refresh access token

### Attendance
- `POST /api/attendance/check-in` - Check in for the day
- `POST /api/attendance/check-out` - Check out
- `GET /api/attendance/today` - Get today's attendance
- `GET /api/attendance/history` - Get attendance history
- `GET /api/attendance/stats` - Get attendance statistics

### Leave Management
- `GET /api/leave/balance` - Get leave balance
- `POST /api/leave/apply` - Apply for leave
- `GET /api/leave/history` - Get leave history

### Timesheet
- `POST /api/timesheet/create` - Create timesheet
- `POST /api/timesheet/<id>/add-entry` - Add entry to timesheet
- `POST /api/timesheet/<id>/submit` - Submit timesheet

### Support Tickets
- `POST /api/tickets/create` - Create support ticket
- `GET /api/tickets` - Get tickets

### Employee Profile
- `GET /api/profile` - Get employee profile
- `PUT /api/profile/update` - Update profile

### HR/Admin (Requires HR or Admin role)
- `GET /api/admin/employees` - Get all employees
- `GET /api/admin/team-attendance` - Get team attendance
- `GET /api/admin/leave-approvals` - Get pending approvals
- `POST /api/admin/approve-leave/<id>` - Approve leave
- `POST /api/admin/reject-leave/<id>` - Reject leave
- `GET /api/admin/dashboard-stats` - Get dashboard stats

## Sample API Requests

### Register
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "EMP5834",
    "email": "john@otsi-global.com",
    "full_name": "John Doe",
    "password": "securepassword123"
  }'
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "EMP5834",
    "password": "securepassword123",
    "role": "employee"
  }'
```

### Check In
```bash
curl -X POST http://localhost:5000/api/attendance/check-in \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "latitude": 17.4474,
    "longitude": 78.3762,
    "is_wfh": false
  }'
```

### Apply Leave
```bash
curl -X POST http://localhost:5000/api/leave/apply \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "leave_type": "casual",
    "start_date": "2026-06-15",
    "end_date": "2026-06-17",
    "reason": "Personal work"
  }'
```

## Database Schema

### Tables
1. **employees** - Employee master data
2. **attendance_logs** - Daily attendance records
3. **leave_balance** - Leave balance for each employee
4. **leave_applications** - Leave requests
5. **timesheets** - Timesheet submissions
6. **timesheet_entries** - Individual timesheet entries
7. **support_tickets** - IT support tickets
8. **notifications** - System notifications
9. **audit_logs** - Activity audit trail

## Deployment

### Deployment to Production

#### Option 1: Heroku
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set SUPABASE_URL=your_url
heroku config:set SUPABASE_KEY=your_key
heroku config:set JWT_SECRET_KEY=your_secret

# Deploy
git push heroku main
```

#### Option 2: Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

Build and run:
```bash
docker build -t otsi-attendance-api .
docker run -p 5000:5000 -e SUPABASE_URL=... -e SUPABASE_KEY=... otsi-attendance-api
```

#### Option 3: Traditional VPS
```bash
# SSH into server
ssh user@your-server.com

# Clone repo
git clone your-repo-url
cd ESS\ Backend

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup nginx
# Create systemd service for gunicorn

# Run with gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 app:app
```

## Frontend Integration

Update your HTML file with the backend URL:

```javascript
const API_URL = 'http://localhost:5000/api';  // Development
// const API_URL = 'https://your-api-domain.com/api';  // Production

// Example API call
async function login(email, password, role) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      identifier: email,
      password: password,
      role: role
    })
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  return data;
}
```

## File Structure

```
ESS_Backend/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── auth.py              # Authentication utilities
├── database.py          # Supabase database wrapper
├── utils.py             # Business logic utilities
├── requirements.txt     # Python dependencies
├── database_schema.sql  # Database schema
├── .env.example         # Environment variables template
├── .env                 # Environment variables (not in git)
├── README.md            # This file
└── deployment/
    ├── Dockerfile       # Docker configuration
    ├── docker-compose.yml
    └── nginx.conf       # Nginx configuration
```

## Troubleshooting

### "SUPABASE_URL not set"
- Make sure `.env` file exists in the correct directory
- Check that you've set all environment variables
- Run `echo $SUPABASE_URL` to verify

### Database connection errors
- Verify Supabase URL and API key are correct
- Check that database tables exist (run schema SQL)
- Ensure Supabase project is active

### CORS errors
- Check that frontend URL is in CORS_ORIGINS
- Ensure requests include `Content-Type: application/json`
- Verify Authorization header format: `Bearer YOUR_TOKEN`

### Location verification fails
- Check latitude/longitude precision
- Verify OFFICE_LAT and OFFICE_LNG in config
- Ensure coordinates are within 500m radius

## Development Tips

### Enable Debug Mode
Set `FLASK_DEBUG=True` in `.env` for auto-reloading

### Test Authentication
```python
# Run in Python shell
from auth import AuthUtils
token = AuthUtils.create_access_token('EMP5831', 'employee')
payload = AuthUtils.verify_token(token)
```

### Database Queries
```python
# Run in Python shell
from database import SupabaseDB
records = SupabaseDB.select('employees', '*')
print(records)
```

## Support & Contact

For issues or questions:
- Create an issue in the repository
- Contact: support@otsi-global.com
- Documentation: https://docs.otsi-global.com

## License

Proprietary - OTSI (Object Technology Solutions India)

## Version

v1.0.0 - Initial Release

---

Last Updated: 2026-06-11
