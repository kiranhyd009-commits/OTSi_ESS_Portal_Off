# OTSI Attendance Portal - Deployment Guide

Complete guide for deploying the backend to production.

## Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] Database schema created and tested
- [ ] API tested locally (all endpoints)
- [ ] Security review completed
- [ ] SSL certificate ready (if applicable)
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Team trained on operations

## Deployment Options

## Option 1: Heroku (Recommended for Quick Start)

### Prerequisites
- Heroku account (https://www.heroku.com)
- Heroku CLI installed
- Git repository initialized

### Steps

```bash
# 1. Login to Heroku
heroku login

# 2. Create Heroku app
heroku create otsi-attendance-api

# 3. Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set JWT_SECRET_KEY=your-super-secret-key
heroku config:set SUPABASE_URL=https://your-project.supabase.co
heroku config:set SUPABASE_KEY=your-supabase-api-key
heroku config:set CORS_ORIGINS=https://yourdomain.com

# 4. Deploy
git push heroku main

# 5. View logs
heroku logs --tail

# 6. Test
curl https://otsi-attendance-api.herokuapp.com/api/health
```

### Monitoring
```bash
# View metrics
heroku metrics

# View logs
heroku logs

# Scale dynos
heroku ps:scale web=2
```

---

## Option 2: Docker on VPS

### Prerequisites
- Server with Ubuntu 20.04+
- Docker and Docker Compose installed
- Domain name
- SSH access

### Setup Steps

```bash
# 1. SSH into server
ssh user@your-server.com

# 2. Clone repository
git clone https://github.com/yourusername/otsi-attendance-api.git
cd otsi-attendance-api/ESS\ Backend

# 3. Create .env file
cp .env.example .env
# Edit .env with production values
nano .env

# 4. Build Docker image
docker build -t otsi-attendance-api:latest .

# 5. Start container
docker-compose up -d

# 6. Verify
curl http://localhost:5000/api/health
```

### Nginx Reverse Proxy

Create `/etc/nginx/sites-available/otsi-api`:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy settings
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/otsi-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Setup SSL with Let's Encrypt:
```bash
sudo certbot certonly --nginx -d api.yourdomain.com
```

---

## Option 3: AWS EC2

### Prerequisites
- AWS account
- EC2 instance running Ubuntu 20.04
- Security group configured

### Steps

```bash
# 1. Connect to EC2
ssh -i your-key.pem ubuntu@your-instance-ip

# 2. Update system
sudo apt update && sudo apt upgrade -y

# 3. Install dependencies
sudo apt install -y python3-pip python3-venv git docker.io docker-compose

# 4. Clone and setup
git clone https://github.com/yourusername/otsi-attendance-api.git
cd otsi-attendance-api/ESS\ Backend

# 5. Configure
cp .env.example .env
nano .env  # Edit with production values

# 6. Build and run
docker-compose up -d

# 7. Setup Nginx and SSL (see Option 2)
```

---

## Option 4: AWS Lambda + API Gateway (Serverless)

### Prerequisites
- AWS account
- SAM CLI installed
- AWS Lambda Python 3.9 runtime

### Steps

Create `template.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  AttendanceAPI:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod
      Name: otsi-attendance-api

  AttendanceFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.lambda_handler
      Runtime: python3.9
      CodeUri: .
      Events:
        ApiEvent:
          Type: Api
          Properties:
            RestApiId: !Ref AttendanceAPI
            Path: /{proxy+}
            Method: ANY
      Environment:
        Variables:
          SUPABASE_URL: !Sub '{{resolve:secretsmanager:supabase-url}}'
          SUPABASE_KEY: !Sub '{{resolve:secretsmanager:supabase-key}}'
```

Deploy:
```bash
sam build
sam deploy --guided
```

---

## Production Configuration

### Environment Variables

```env
# Flask
FLASK_ENV=production
FLASK_DEBUG=False

# Security
JWT_SECRET_KEY=generate-a-strong-random-key
SECRET_KEY=generate-a-strong-random-key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-production-key

# CORS - Only production domain
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Server
SERVER_PORT=5000
SERVER_HOST=0.0.0.0

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### Security Hardening

#### 1. Enable Row Level Security (RLS) in Supabase

```sql
-- Enable RLS on all tables
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance_logs ENABLE ROW LEVEL SECURITY;

-- Example policy: Employees can only see their own data
CREATE POLICY "Users can view their own data"
ON attendance_logs FOR SELECT
USING (
  employee_id = current_user_id()
);
```

#### 2. Configure Firewall Rules

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

#### 3. SSL/TLS Configuration

```python
# In production, enforce HTTPS
@app.before_request
def enforce_https():
    if not request.is_secure and not app.debug:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)
```

#### 4. Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # ...
```

### Monitoring & Logging

#### 1. Application Monitoring

```python
import logging
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
```

#### 2. Error Tracking

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1
)
```

#### 3. Performance Monitoring

```python
# NewRelic APM
import newrelic.agent
newrelic.agent.initialize('newrelic.ini')

@app.route('/api/health')
@newrelic.agent.function_trace()
def health_check():
    # ...
```

### Database Backup

#### Automated Backups (Supabase handles this)

1. Go to Database > Backups in Supabase dashboard
2. Enable daily automated backups
3. Configure retention period

#### Manual Backup

```bash
# Backup database
pg_dump -h your-db.supabase.co \
  -U postgres \
  -d your_db > backup.sql

# Restore
psql -h your-db.supabase.co \
  -U postgres \
  -d your_db < backup.sql
```

### Performance Optimization

#### 1. Enable Caching

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/attendance/stats')
@cache.cached(timeout=3600)
def get_stats():
    # ...
```

#### 2. Database Query Optimization

```python
# Use batch queries
records = SupabaseDB.select('attendance_logs', '*',
                           {'attendance_date': ('gte', '2026-01-01')})

# Limit results
records = SupabaseDB.select('attendance_logs', '*',
                           filters={'employee_id': emp_id})[:100]
```

#### 3. Load Balancing

With multiple instances:

```nginx
upstream api_servers {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://api_servers;
    }
}
```

### Scaling

#### Horizontal Scaling

```bash
# Start multiple instances
gunicorn --workers 8 --bind 0.0.0.0:5000 app:app
gunicorn --workers 8 --bind 0.0.0.0:5001 app:app
gunicorn --workers 8 --bind 0.0.0.0:5002 app:app

# Or with Docker
docker-compose up --scale api=3
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Test all endpoints in staging
- [ ] Load test the application
- [ ] Review security
- [ ] Database backups configured
- [ ] Monitoring configured
- [ ] Rollback plan documented

### Deployment
- [ ] Deploy to production
- [ ] Verify health check passes
- [ ] Run smoke tests
- [ ] Monitor error rates
- [ ] Check performance metrics

### Post-Deployment
- [ ] Verify all endpoints working
- [ ] Test with real user account
- [ ] Monitor logs for errors
- [ ] Check CPU/Memory usage
- [ ] Verify backups are running
- [ ] Notify team of deployment

---

## Rollback Procedure

If deployment fails:

```bash
# Docker rollback
docker-compose down
docker-compose up -d  # Start previous version

# Git rollback
git revert last-commit-hash
git push

# Heroku rollback
heroku releases
heroku rollback v123
```

---

## Maintenance

### Regular Tasks

- [ ] Check application logs daily
- [ ] Monitor performance metrics
- [ ] Review error rates
- [ ] Update dependencies monthly
- [ ] Review security updates
- [ ] Test backup/restore procedures
- [ ] Performance tuning

### Monthly Maintenance Window

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Run security audit
pip audit

# Clear old logs
find logs -mtime +30 -delete

# Restart application
systemctl restart otsi-attendance-api
```

---

## Support Contacts

- Production Issue: ops@otsi-global.com
- Security: security@otsi-global.com
- General: support@otsi-global.com

---

**Version:** 1.0.0  
**Last Updated:** 2026-06-11
