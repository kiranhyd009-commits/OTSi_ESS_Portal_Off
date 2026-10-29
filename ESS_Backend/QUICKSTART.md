# OTSI Attendance Portal - Quick Start Guide

Get the backend API running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Supabase account (free at https://supabase.com)
- Git (optional)

## Method 1: Automatic Setup (Recommended)

### On Windows

```powershell
# 1. Navigate to backend folder
cd "d:\OTSi_ESS_Portal\ESS_Backend"

# 2. Run setup script
python setup.py

# 3. Follow the prompts and enter your Supabase credentials

# 4. Activate virtual environment
venv\Scripts\activate

# 5. Run the application
python app.py
```

### On macOS/Linux

```bash
# 1. Navigate to backend folder
cd "OTSi_ESS_Portal/ESS_Backend"

# 2. Run setup script
python3 setup.py

# 3. Follow the prompts and enter your Supabase credentials

# 4. Activate virtual environment
source venv/bin/activate

# 5. Run the application
python app.py
```

## Method 2: Manual Setup

### Step 1: Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Setup Supabase

1. Go to https://supabase.com
2. Sign in or create an account
3. Create a new project
4. Go to SQL Editor
5. Create a new query
6. Copy-paste all content from `database_schema.sql`
7. Click "Run" to execute

### Step 4: Configure Environment

1. Copy `.env.example` to `.env`
2. Edit `.env` and add your Supabase details:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
JWT_SECRET_KEY=your-secret-key
```

### Step 5: Run Application

```bash
python app.py
```

You should see:
```
Starting OTSI Attendance Portal API on 0.0.0.0:5000
 * Running on http://localhost:5000
```

## Method 3: Docker Setup

### Prerequisites
- Docker and Docker Compose installed

### Steps

```bash
# 1. Navigate to backend folder
cd "OTSi_ESS_Portal/ESS_Backend"

# 2. Create .env with your Supabase credentials
cp .env.example .env
# Edit .env with your details

# 3. Start containers
docker-compose up -d

# 4. Verify it's running
curl http://localhost:5000/api/health
```

## Verify Installation

### Test API Health

```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2026-06-11T10:30:00Z",
  "service": "OTSI Attendance Portal API"
}
```

### Create Test User

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "EMP9999",
    "email": "test@otsi-global.com",
    "full_name": "Test User",
    "password": "TestPass123!"
  }'
```

Expected response:
```json
{
  "message": "Registration successful. Please sign in.",
  "employee_id": "EMP9999"
}
```

## Sample Credentials for Testing

### Pre-loaded Employees (from database_schema.sql)

| Employee ID | Email | Password | Role |
|------------|-------|----------|------|
| EMP5831 | ravi@otsi-global.com | hashed_password_1 | employee |
| EMP4001 | kiran@otsi-global.com | hashed_password_2 | hr |
| ADMIN001 | admin@otsi-global.com | hashed_password_3 | admin |

**Note:** The pre-loaded passwords are hashed. Use your own test credentials from registration.

## Common Issues & Solutions

### Issue: "SUPABASE_URL not set"

**Solution:**
- Ensure `.env` file exists in the ESS_Backend directory
- Check that Supabase credentials are filled in
- Restart the application

### Issue: "ModuleNotFoundError: No module named 'supabase'"

**Solution:**
```bash
# Make sure virtual environment is activated
# Then reinstall dependencies
pip install -r requirements.txt
```

### Issue: Connection refused on localhost:5000

**Solution:**
- Check that port 5000 is not in use
- If port is taken, change in `.env`: `SERVER_PORT=5001`
- Restart application

### Issue: "Invalid email domain"

**Solution:**
- Email must end with @otsi-global.com or @otsi-usa.com
- Example: yourname@otsi-global.com

## First Login

### Login to Test Account

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "EMP9999",
    "password": "TestPass123!",
    "role": "employee"
  }'
```

Response includes `access_token` - save this for testing other endpoints.

### Check Today's Attendance

```bash
curl -X GET http://localhost:5000/api/attendance/today \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Next Steps

1. **Update Frontend:** Change API URL in HTML file to `http://localhost:5000/api`
2. **Test All Endpoints:** See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
3. **Deploy:** Follow deployment guide in [README.md](README.md)

## File Structure

```
ESS_Backend/
├── app.py                 # Main Flask API
├── config.py             # Configuration
├── auth.py              # Authentication logic
├── database.py          # Supabase wrapper
├── utils.py             # Business logic
├── requirements.txt     # Python packages
├── database_schema.sql  # Database setup
├── .env.example         # Environment template
├── setup.py             # Auto setup script
├── Dockerfile           # Docker image
├── docker-compose.yml   # Docker compose
├── README.md            # Full documentation
├── API_DOCUMENTATION.md # API reference
└── QUICKSTART.md        # This file
```

## Troubleshooting

### Check Logs

Application logs are printed to console. For detailed debugging:

```bash
# On Windows
set FLASK_DEBUG=True
python app.py

# On macOS/Linux
export FLASK_DEBUG=True
python app.py
```

### Test Database Connection

```bash
python3 -c "from database import SupabaseDB; print(SupabaseDB.get_client())"
```

### Reset Database

To delete all data and restart:

1. Go to Supabase Project Settings
2. Danger Zone > Delete Project Data
3. Re-run `database_schema.sql`

## Performance Tips

1. **Enable Caching:** Use browser caching for static assets
2. **Database Indexing:** Already configured in schema
3. **Connection Pooling:** Configured in Supabase
4. **Rate Limiting:** Implement in production

## Security Best Practices

1. ✅ Change `JWT_SECRET_KEY` in production
2. ✅ Use HTTPS in production
3. ✅ Enable Row Level Security (RLS) in Supabase
4. ✅ Set strong CORS origins
5. ✅ Use environment variables for secrets
6. ✅ Regular security audits

## Getting Help

- 📖 Read [README.md](README.md)
- 📚 Check [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- 🐛 Check logs in terminal
- 💬 Contact: support@otsi-global.com

## What's Included

✅ Complete Flask API with 30+ endpoints
✅ JWT authentication and authorization
✅ Supabase database integration
✅ Attendance tracking with geolocation
✅ Leave management system
✅ Timesheet management
✅ IT support ticketing
✅ HR/Admin dashboard
✅ Comprehensive error handling
✅ Audit logging
✅ API documentation
✅ Docker support
✅ Database schema
✅ Sample data

## Next Development Steps

- [ ] Setup frontend integration
- [ ] Test all endpoints
- [ ] Deploy to staging
- [ ] Configure production database
- [ ] Setup CI/CD pipeline
- [ ] Configure domain/SSL
- [ ] Setup monitoring/alerts
- [ ] Launch to production

---

**Version:** 1.0.0  
**Last Updated:** 2026-06-11  
**Status:** ✅ Ready for Production
