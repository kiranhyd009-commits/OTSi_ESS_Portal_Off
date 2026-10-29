# 💻 OTSi ESS Portal - Personal Laptop Complete Setup Guide

This guide details how to set up and run the entire **OTSi ESS Portal** project on your personal laptop from scratch.

---

## ⚡ Quick 1-Click Setup (Windows)

1. Open PowerShell / Command Prompt.
2. Navigate to your project folder:
   ```cmd
   cd OTSi_ESS_Portal
   ```
3. Run the automated master setup script:
   ```cmd
   setup_laptop.bat
   ```
4. The script will automatically:
   - Verify your Python installation.
   - Create a clean virtual environment (`venv`).
   - Install all required Python packages from `requirements.txt`.
   - Create the configuration `.env` file automatically.
   - Offer to launch the server immediately.

---

## 🛠️ Step-by-Step Setup Guide

### Step 1: Prerequisites
Ensure your personal laptop has Python installed:
- **Python 3.8+**: Download from [python.org](https://www.python.org/downloads/).
  - **Important:** On Windows, make sure to check the option: **"Add Python to PATH"** during installation.

---

### Step 2: Database Setup (Supabase - Free)

1. Go to [https://supabase.com](https://supabase.com) and create a free account.
2. Click **New Project** and set your database password.
3. Once initialized, navigate to **Project Settings** → **API**:
   - Copy **Project URL** (e.g. `https://xyzcompany.supabase.co`)
   - Copy **anon / public key** (or `service_role` key)
4. Go to **SQL Editor** (left sidebar menu) → Click **New Query**.
5. Copy the contents of [`ESS_Backend/database_schema.sql`](file:///d:/OTSi_ESS_Portal/ESS_Backend/database_schema.sql), paste into the editor, and click **Run**.

---

### Step 3: Configure Environment Variables

Open or edit `ESS_Backend/.env` on your laptop:

```env
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_APP=app.py

JWT_SECRET_KEY=otsi-personal-laptop-secret-key-2026

SUPABASE_URL=https://YOUR_PROJECT_SUBDOMAIN.supabase.co
SUPABASE_KEY=YOUR_SUPABASE_API_KEY_HERE

CORS_ORIGINS=http://localhost:5000,http://localhost:3000,http://127.0.0.1:5000
SERVER_PORT=5000
SERVER_HOST=0.0.0.0
```

---

### Step 4: Running the Portal

#### Option A: Double-Click Batch Launcher (Windows)
Double-click `start_server.bat` in the project root folder.

#### Option B: Terminal Command
```bash
# Navigate to backend folder
cd ESS_Backend

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac / Linux:
source venv/bin/activate

# Start the Flask API server
python app.py
```

The backend server will run at: `http://127.0.0.1:5000`

---

### Step 5: Access the Frontend Portal

- Double click and open `otsi-attendance-portal.html` directly in Google Chrome, Microsoft Edge, or Safari.
- Alternatively, visit `http://127.0.0.1:5000` in your web browser.

---

## 👥 Default Test Logins

| Role | Email | Password |
|---|---|---|
| **Employee** | `ravi.mallem@otsi.co.in` | `R@vikiran332` |
| **Leadership / Admin** | `kiran.us009@gmail.com` | `R@vikiran332` |
| **Admin** | `admin.otsi@otsi-usa.com` | `R@vikiran332!` |

---

## 🔍 Troubleshooting Tips
- **Python not recognized:** Re-install Python and ensure "Add Python to PATH" is checked.
- **Port 5000 in use:** Edit `SERVER_PORT=5001` in `ESS_Backend/.env`.
- **Database Connection Errors:** Verify `SUPABASE_URL` and `SUPABASE_KEY` inside `ESS_Backend/.env`.
