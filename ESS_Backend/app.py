"""
OTSI Attendance Portal - Flask Backend API
Full-stack backend with Supabase integration
"""
import os
import threading
import logging
import csv
import io
import secrets
from collections import defaultdict
from datetime import datetime, date, timedelta, timezone
from functools import wraps

from flask import Flask, request, jsonify, send_file, make_response, g
from flask_cors import CORS
from dotenv import load_dotenv

from config import config_by_name
from database import SupabaseDB
from auth import AuthUtils, token_required, role_required, TokenBlacklist
from utils import (
    LocationUtils, AttendanceUtils, LeaveUtils, TimesheetUtils,
    NotificationUtils, EmailService, log_audit
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config_by_name.get(FLASK_ENV, 'development'))

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})  # type: ignore[arg-type]

# ═════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═════════════════════════════════════════════════════════════

@app.route('/', methods=['GET'])
def frontend():
    """Serve the attendance portal frontend."""
    frontend_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'otsi-attendance-portal.html')
    )
    response = make_response(send_file(frontend_path))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/images/<path:filename>', methods=['GET'])
def serve_image(filename):
    """Serve image assets."""
    images_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'images'))
    return send_file(os.path.join(images_dir, filename))


@app.route('/manifest.json', methods=['GET'])
def manifest():
    """Serve PWA manifest."""
    manifest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'manifest.json'))
    response = make_response(send_file(manifest_path, mimetype='application/manifest+json'))
    response.headers['Cache-Control'] = 'no-cache'
    return response


@app.route('/sw.js', methods=['GET'])
def service_worker():
    """Serve PWA service worker with root scope."""
    sw_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sw.js'))
    response = make_response(send_file(sw_path, mimetype='application/javascript'))
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response


@app.route('/favicon.ico', methods=['GET'])
def favicon():
    """Silence favicon.ico 404 warning logs."""
    return '', 204


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'OTSI Attendance Portal API'
    }), 200


# ═════════════════════════════════════════════════════════════
# AUTHENTICATION / ADMIN BOOTSTRAP HELPERS
# ═════════════════════════════════════════════════════════════


def ensure_default_otsi_admin(password: str | None = None) -> dict:
    """Create or update the fixed OTSI admin account."""
    employee_id = 'OTSI0001'
    email = 'admin.otsi@otsi-usa.com'
    now = datetime.now(timezone.utc).isoformat()
    temp_password = password or secrets.token_urlsafe(10)
    password_hash = AuthUtils.hash_password(temp_password)

    existing_by_id = SupabaseDB.select_one('employees', {'employee_id': employee_id})
    existing_by_email = SupabaseDB.select_one('employees', {'email': email})
    existing = existing_by_id or existing_by_email

    record = {
        'employee_id': employee_id,
        'email': email,
        'full_name': 'OTSI Administrator',
        'designation': 'System Administrator',
        'department': 'Administration',
        'password_hash': password_hash,
        'role': 'admin',
        'status': 'active',
        'date_of_joining': date.today().isoformat(),
        'updated_at': now,
        'password_changed_at': now,
        'failed_login_attempts': 0,
        'lockout_until': None,
        'mfa_enabled': True,
        'mfa_temp_code': None,
        'mfa_temp_expires': None
    }

    if existing:
        SupabaseDB.update('employees', {'employee_id': existing['employee_id']}, record)
        created = SupabaseDB.select_one('employees', {'employee_id': employee_id})
    else:
        record['created_at'] = now
        created = SupabaseDB.insert('employees', record)

    leave_balance = SupabaseDB.select_one('leave_balance', {'employee_id': employee_id})
    if not leave_balance:
        SupabaseDB.insert('leave_balance', {
            'employee_id': employee_id,
            'casual_leave': 12,
            'sick_leave': 8,
            'earned_leave': 20.0,
            'bereavement_leave': 3,
            'marriage_leave': 0,
            'lop_leave': 0,
            'created_at': now,
            'updated_at': now
        })

    try:
        SupabaseDB.insert('password_history', {
            'employee_id': employee_id,
            'password_hash': password_hash,
            'created_at': now
        })
    except Exception as history_error:
        logger.warning(f"Failed to store password history for default OTSI admin: {history_error}")

    log_audit(employee_id, 'ENSURE_DEFAULT_OTSI_ADMIN', 'employees', new_values={
        'employee_id': employee_id,
        'email': email,
        'role': 'admin',
        'status': 'active'
    })

    return {
        'employee_id': employee_id,
        'email': email,
        'password': temp_password,
        'created': created
    }


def get_scope_context(current_emp_id: str):
    """Return scope info for HR/Admin/Manager style access."""
    current_emp = SupabaseDB.select_one('employees', {'employee_id': current_emp_id})
    is_hr = bool(current_emp and current_emp.get('role') in ['hr', 'admin'])
    reports = SupabaseDB.select('employees', '*', {'manager_id': current_emp_id})
    report_ids = [r['employee_id'] for r in reports]
    is_manager = len(report_ids) > 0
    return current_emp, is_hr, is_manager, reports, report_ids


def classify_employee_record(emp: dict) -> str:
    """Classify employee status for admin views."""
    if emp.get('status') == 'inactive' and not emp.get('designation') and not emp.get('manager_id'):
        return 'pending'
    return emp.get('status', 'active')


def is_mfa_enabled_globally() -> bool:
    """Check whether MFA is currently enabled for the application."""
    return bool(app.config.get('MFA_ENABLED', True))


def is_system_admin_account(employee: dict | None) -> bool:
    """Identify the dedicated OTSI top-level admin login."""
    if not employee:
        return False
    return (
        employee.get('role') == 'admin'
        and employee.get('employee_id') == 'OTSI0001'
        and (employee.get('email') or '').lower() == 'admin.otsi@otsi-usa.com'
    )


# ═════════════════════════════════════════════════════════════
# AUTHENTICATION ENDPOINTS
# ═════════════════════════════════════════════════════════════

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new employee account"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['employee_id', 'email', 'full_name', 'password']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        employee_id = data['employee_id'].strip().upper()
        email = data['email'].strip().lower()
        full_name = data['full_name'].strip()
        password = data['password']
        
        # Validate Employee ID format: EMP + 4 digits, or ADMIN + digits
        import re
        # Allow EMP####, ADMIN*, or OTSI#### (OTSI series added for new employee IDs)
        if not re.match(r'^EMP\d{4}$', employee_id) and not re.match(r'^ADMIN\d+$', employee_id) and not re.match(r'^OTSI\d{4}$', employee_id):
            return jsonify({'error': 'Employee ID must be EMP followed by 4 digits (e.g. EMP1001), ADMIN prefix, or OTSI followed by 4 digits (e.g. OTSI0001)'}), 400
        
        # Validate email domain — only @otsi-usa.com and @otsi.co.in
        valid_domains = ['otsi-usa.com', 'otsi.co.in']
        if not any(email.endswith(f'@{domain}') for domain in valid_domains):
            return jsonify({'error': 'Only @otsi-usa.com or @otsi.co.in email addresses are allowed'}), 400

        # Validate name.surname format in local part
        local_part = email.split('@')[0]
        if '.' not in local_part or local_part.startswith('.') or local_part.endswith('.'):
            return jsonify({'error': 'Email must follow the format name.surname@otsi-usa.com'}), 400
        
        # Check if employee already exists
        existing = SupabaseDB.select_one('employees', {'employee_id': employee_id})
        if existing:
            return jsonify({'error': 'Employee ID already registered'}), 400
        
        existing_email = SupabaseDB.select_one('employees', {'email': email})
        if existing_email:
            return jsonify({'error': 'Email already registered'}), 400
        
        # Validate password policy
        is_valid, policy_err = AuthUtils.validate_password_policy(password, email, full_name, employee_id)
        if not is_valid:
            return jsonify({'error': policy_err}), 400
        
        # Hash password and create employee
        password_hash = AuthUtils.hash_password(password)
        
        employee_data = {
            'employee_id': employee_id,
            'email': email,
            'full_name': full_name,
            'password_hash': password_hash,
            'role': 'employee',
            'status': 'inactive',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'password_changed_at': datetime.now(timezone.utc).isoformat(),
            'failed_login_attempts': 0,
            'mfa_enabled': False
        }
        
        if 'team' in data:
            employee_data['team'] = data['team']
        if 'department' in data:
            employee_data['department'] = data['department']
        
        employee = SupabaseDB.insert('employees', employee_data)
        
        # Insert initial password history
        try:
            SupabaseDB.insert('password_history', {
                'employee_id': employee_id,
                'password_hash': password_hash,
                'created_at': datetime.now(timezone.utc).isoformat()
            })
        except Exception as he:
            logger.error(f"Failed to insert password history during register: {he}")
        
        # Create leave balance record
        leave_balance_data = {
            'employee_id': employee_id,
            'casual_leave': 12,
            'sick_leave': 8,
            'earned_leave': 20.0,
            'bereavement_leave': 3,
            'marriage_leave': 0,
            'lop_leave': 0
        }
        SupabaseDB.insert('leave_balance', leave_balance_data)
        
        log_audit(employee_id, 'REGISTER', 'employee', new_values=employee_data)
        
        # Notify HR
        hr_users = SupabaseDB.select('employees', 'employee_id', {'role': 'hr'})
        admin_users = SupabaseDB.select('employees', 'employee_id', {'role': 'admin'})
        hr_ids = [u['employee_id'] for u in hr_users + admin_users]
        for nid in set(hr_ids):
            NotificationUtils.create_notification(
                nid,
                'New Employee Registration',
                f'Pending Registration: {full_name} ({employee_id}) is awaiting your approval.',
                'new_employee',
                action_url='profile'
            )
        
        return jsonify({
            'message': 'Registration successful. Please sign in.',
            'employee_id': employee_id
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500


# Development helper: create or update a super-admin directly (local-only)
@app.route('/api/dev/create-super-admin', methods=['POST'])
def dev_create_super_admin():
    """Create or update a super-admin account directly in the DB. Local-only endpoint for development convenience."""
    try:
        remote = request.remote_addr or ''
        if remote not in ('127.0.0.1', '::1', 'localhost'):
            return jsonify({'error': 'Not allowed from remote hosts'}), 403

        data = request.get_json() or {}
        required = ['employee_id', 'email', 'full_name', 'password']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400

        employee_id = data['employee_id'].strip().upper()
        email = data['email'].strip().lower()
        full_name = data['full_name'].strip()
        password = data['password']
        now = datetime.now(timezone.utc).isoformat()
        password_hash = AuthUtils.hash_password(password)

        employee = SupabaseDB.select_one('employees', {'employee_id': employee_id})
        record = {
            'employee_id': employee_id,
            'email': email,
            'full_name': full_name,
            'password_hash': password_hash,
            'role': 'admin',
            'status': 'active',
            'updated_at': now,
            'password_changed_at': now,
            'failed_login_attempts': 0,
            'lockout_until': None,
            'mfa_enabled': True,
            'mfa_temp_code': None,
            'mfa_temp_expires': None
        }

        if employee:
            SupabaseDB.update('employees', {'employee_id': employee_id}, record)
        else:
            record['created_at'] = now
            SupabaseDB.insert('employees', record)

        lb = SupabaseDB.select_one('leave_balance', {'employee_id': employee_id})
        if not lb:
            SupabaseDB.insert('leave_balance', {
                'employee_id': employee_id,
                'casual_leave': 12,
                'sick_leave': 8,
                'earned_leave': 20.0,
                'bereavement_leave': 3,
                'marriage_leave': 0,
                'lop_leave': 0,
                'created_at': now,
                'updated_at': now
            })

        log_audit(employee_id, 'CREATE_SUPER_ADMIN', 'employees', new_values={
            'employee_id': employee_id,
            'email': email,
            'role': 'admin',
            'status': 'active'
        })

        return jsonify({'message': 'Super-admin created/updated', 'employee_id': employee_id}), 201
    except Exception as e:
        logger.error(f"Dev create super-admin error: {str(e)}")
        return jsonify({'error': 'Failed to create super-admin'}), 500


@app.route('/api/dev/bootstrap-otsi-admin', methods=['POST'])
def bootstrap_otsi_admin():
    """Create or reset the fixed OTSI admin login. Local-only for development/setup."""
    try:
        remote = request.remote_addr or ''
        if remote not in ('127.0.0.1', '::1', 'localhost'):
            return jsonify({'error': 'Not allowed from remote hosts'}), 403

        data = request.get_json() or {}
        result = ensure_default_otsi_admin(data.get('password'))
        return jsonify({
            'message': 'Default OTSI admin account is ready.',
            'employee_id': result['employee_id'],
            'email': result['email'],
            'temporary_password': result['password']
        }), 201
    except Exception as e:
        logger.error(f"Bootstrap OTSI admin error: {str(e)}")
        return jsonify({'error': 'Failed to bootstrap OTSI admin'}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login employee"""
    try:
        data = request.get_json()
        
        if not data or not data.get('identifier') or not data.get('password'):
            return jsonify({'error': 'Missing credentials'}), 400
        
        identifier = data['identifier'].strip().upper()
        password = data['password']
        role = data.get('role')
        
        # Find employee by ID or email
        employee = SupabaseDB.select_one('employees', {'employee_id': identifier})
        if not employee:
            employee = SupabaseDB.select_one('employees', {'email': identifier.lower()})
        
        if not employee:
            return jsonify({'error': 'Invalid credentials'}), 401
            
        # Check employee status
        status = employee.get('status', 'active')
        if status == 'inactive':
            # Check if they are pending (no manager_id / designation / department)
            if not employee.get('manager_id') and not employee.get('designation'):
                return jsonify({'error': 'Your registration is currently under review by the administration. Access will be enabled shortly.'}), 403
            else:
                return jsonify({'error': 'This employee account is currently deactivated.'}), 403
        
        # 1. Check account lockout status
        from dateutil.parser import parse
        lockout_until = employee.get('lockout_until')
        if lockout_until:
            lockout_dt = parse(lockout_until).replace(tzinfo=timezone.utc)
            if lockout_dt > datetime.now(timezone.utc):
                remaining = int((lockout_dt - datetime.now(timezone.utc)).total_seconds() / 60)
                remaining = max(1, remaining)
                return jsonify({'error': f"Account is locked due to multiple failed login attempts. Try again in {remaining} minutes."}), 403
        
        # 2. Verify password
        if not AuthUtils.verify_password(password, employee['password_hash']):
            failed_attempts = employee.get('failed_login_attempts', 0) or 0
            failed_attempts += 1
            
            update_data = {'failed_login_attempts': failed_attempts}
            
            if failed_attempts >= 5:
                # Lockout for 15 minutes
                lockout_time = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
                update_data['lockout_until'] = lockout_time
                SupabaseDB.update('employees', {'employee_id': employee['employee_id']}, update_data)
                return jsonify({'error': "Account locked for 15 minutes due to 5 failed login attempts."}), 403
            else:
                SupabaseDB.update('employees', {'employee_id': employee['employee_id']}, update_data)
                attempts_left = 5 - failed_attempts
                return jsonify({'error': f"Invalid credentials. {attempts_left} attempts remaining."}), 401
        
        # Verify role matches only when a role is explicitly requested
        if role and employee['role'] != role:
            return jsonify({'error': f'This account is not registered as {role}'}), 403
        
        # 3. Successful login - Reset lockout/failed attempts
        SupabaseDB.update('employees', 
                         {'employee_id': employee['employee_id']},
                         {
                             'failed_login_attempts': 0,
                             'lockout_until': None,
                             'last_login': datetime.now(timezone.utc).isoformat()
                         })
                         
        # 4. Check password expiration (90 days)
        password_changed_at = employee.get('password_changed_at')
        if password_changed_at:
            changed_dt = parse(password_changed_at).replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - changed_dt > timedelta(days=90):
                # Generate temporary token for password reset
                temp_token = AuthUtils.create_access_token(employee['employee_id'], employee['role'], expires_in=1)
                return jsonify({
                    'password_expired': True,
                    'temp_token': temp_token,
                    'employee_id': employee['employee_id'],
                    'error': 'Your password has expired. Please reset it to continue.'
                }), 200

        # 5. Check if MFA is required (based on feature flag + user setting)
        is_mfa_enabled = is_mfa_enabled_globally() and employee.get('mfa_enabled', False)
        
        if is_mfa_enabled:
            import random
            mfa_code = f"{random.randint(100000, 999999)}"
            mfa_expires = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
            
            SupabaseDB.update('employees',
                             {'employee_id': employee['employee_id']},
                             {
                                 'mfa_temp_code': mfa_code,
                                 'mfa_temp_expires': mfa_expires
                             })
                             
            # Send code via system notification so user can retrieve it inside the bell icon
            NotificationUtils.create_notification(
                employee['employee_id'],
                'MFA Verification Code',
                f'Your login verification code is {mfa_code}. It will expire in 5 minutes.',
                'mfa'
            )
            
            print(f"\n[SECURITY] MFA Verification Code for {employee['employee_id']}: {mfa_code}\n", flush=True)
            
            temp_token = AuthUtils.create_access_token(employee['employee_id'], employee['role'], expires_in=1)
            
            return jsonify({
                'mfa_required': True,
                'temp_token': temp_token,
                'employee_id': employee['employee_id'],
                'message': 'MFA code sent to your notifications.'
            }), 200
        
        # Create tokens
        access_token = AuthUtils.create_access_token(employee['employee_id'], employee['role'])
        refresh_token = AuthUtils.create_refresh_token(employee['employee_id'], employee['role'])
        
        # Check if they have reportees
        reports = SupabaseDB.select('employees', 'employee_id', {'manager_id': employee['employee_id']})
        is_manager = len(reports) > 0
        
        log_audit(employee['employee_id'], 'LOGIN', 'auth')
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'employee': {
                'employee_id': employee['employee_id'],
                'email': employee['email'],
                'full_name': employee['full_name'],
                'role': employee['role'],
                'designation': employee['designation'],
                'is_manager': is_manager
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Login failed: {str(e)}'}), 500


@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout():
    """Logout employee"""
    try:
        token = AuthUtils.get_token_from_request()
        if token:
            TokenBlacklist.add(token)
        
        log_audit(g.current_employee_id, 'LOGOUT', 'auth')
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500


@app.route('/api/auth/mfa-verify', methods=['POST'])
def mfa_verify():
    """Verify MFA code and return tokens"""
    try:
        if not is_mfa_enabled_globally():
            return jsonify({'error': 'MFA is temporarily disabled for this environment.'}), 400

        data = request.get_json()
        employee_id = data.get('employee_id')
        mfa_code = data.get('mfa_code')
        temp_token = data.get('temp_token')
        
        if not employee_id or not mfa_code or not temp_token:
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Verify temp token is valid
        try:
            AuthUtils.verify_token(temp_token)
        except Exception as te:
            return jsonify({'error': f'Invalid session: {str(te)}'}), 401
            
        employee = SupabaseDB.select_one('employees', {'employee_id': employee_id})
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
            
        # Check code and expiration
        saved_code = employee.get('mfa_temp_code')
        expires_at = employee.get('mfa_temp_expires')
        
        if not saved_code or not expires_at:
            return jsonify({'error': 'MFA not initiated or code expired'}), 400
            
        from dateutil.parser import parse
        expires_dt = parse(expires_at).replace(tzinfo=timezone.utc)
        if expires_dt < datetime.now(timezone.utc):
            return jsonify({'error': 'MFA code expired. Please log in again.'}), 400
            
        if saved_code != mfa_code.strip():
            return jsonify({'error': 'Invalid MFA code'}), 401
            
        # Success - clear temp code
        SupabaseDB.update('employees',
                         {'employee_id': employee_id},
                         {
                             'mfa_temp_code': None,
                             'mfa_temp_expires': None
                         })
                         
        # Create full tokens
        access_token = AuthUtils.create_access_token(employee['employee_id'], employee['role'])
        refresh_token = AuthUtils.create_refresh_token(employee['employee_id'], employee['role'])
        
        log_audit(employee['employee_id'], 'MFA_VERIFIED', 'auth')
        
        return jsonify({
            'message': 'MFA verified successfully',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'employee': {
                'employee_id': employee['employee_id'],
                'email': employee['email'],
                'full_name': employee['full_name'],
                'role': employee['role'],
                'designation': employee['designation']
            }
        }), 200
    except Exception as e:
        logger.error(f"MFA verify error: {str(e)}")
        return jsonify({'error': 'Verification failed'}), 500


@app.route('/api/auth/mfa-toggle', methods=['POST'])
@token_required
def mfa_toggle():
    """Toggle MFA enabled status"""
    try:
        if not is_mfa_enabled_globally():
            return jsonify({'message': 'MFA is temporarily disabled application-wide. User preference was not changed.', 'mfa_enabled': False, 'globally_enabled': False}), 200

        data = request.get_json()
        mfa_enabled = data.get('mfa_enabled', False)
        employee_id = g.current_employee_id
        
        employee = SupabaseDB.select_one('employees', {'employee_id': employee_id})
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
            
        # Admin is mandatory only when MFA is enabled globally
        if employee['role'] == 'admin':
            return jsonify({'error': 'MFA is mandatory for Admin accounts when MFA is enabled globally and cannot be disabled individually.'}), 400
            
        SupabaseDB.update('employees',
                         {'employee_id': employee_id},
                         {'mfa_enabled': bool(mfa_enabled)})
                         
        log_audit(employee_id, 'MFA_TOGGLE', 'employee', new_values={'mfa_enabled': mfa_enabled})
        
        return jsonify({'message': f"MFA {'enabled' if mfa_enabled else 'disabled'} successfully"}), 200
    except Exception as e:
        logger.error(f"MFA toggle error: {str(e)}")
        return jsonify({'error': 'Failed to update MFA settings'}), 500


@app.route('/api/auth/change-password', methods=['POST'])
@token_required
def change_password():
    """Change employee password"""
    try:
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not old_password or not new_password or not confirm_password:
            return jsonify({'error': 'Missing required fields'}), 400
            
        if new_password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
            
        employee_id = g.current_employee_id
        employee = SupabaseDB.select_one('employees', {'employee_id': employee_id})
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
            
        # Verify old password
        if not AuthUtils.verify_password(old_password, employee['password_hash']):
            return jsonify({'error': 'Incorrect current password'}), 400
            
        # Validate policy
        is_valid, policy_err = AuthUtils.validate_password_policy(
            new_password, employee['email'], employee['full_name'], employee_id
        )
        if not is_valid:
            return jsonify({'error': policy_err}), 400
            
        # Check history
        is_reused, history_err = AuthUtils.check_password_history(employee_id, new_password)
        if is_reused:
            return jsonify({'error': history_err}), 400
            
        # Update password
        new_hash = AuthUtils.hash_password(new_password)
        SupabaseDB.update('employees',
                         {'employee_id': employee_id},
                         {
                             'password_hash': new_hash,
                             'password_changed_at': datetime.now(timezone.utc).isoformat(),
                             'failed_login_attempts': 0,
                             'lockout_until': None
                         })
                         
        # Add to history
        try:
            SupabaseDB.insert('password_history', {
                'employee_id': employee_id,
                'password_hash': new_hash,
                'created_at': datetime.now(timezone.utc).isoformat()
            })
        except Exception as he:
            logger.error(f"Failed to insert password history: {he}")
            
        log_audit(employee_id, 'PASSWORD_CHANGE', 'employee')
        
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return jsonify({'error': 'Failed to change password'}), 500


@app.route('/api/auth/reset-expired-password', methods=['POST'])
def reset_expired_password():
    """Reset expired password using a temporary token"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        temp_token = data.get('temp_token')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not employee_id or not temp_token or not new_password or not confirm_password:
            return jsonify({'error': 'Missing required fields'}), 400
            
        if new_password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
            
        # Verify temp token
        try:
            AuthUtils.verify_token(temp_token)
        except Exception as te:
            return jsonify({'error': f'Session expired or invalid: {str(te)}'}), 401
            
        employee = SupabaseDB.select_one('employees', {'employee_id': employee_id})
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
            
        # Validate policy
        is_valid, policy_err = AuthUtils.validate_password_policy(
            new_password, employee['email'], employee['full_name'], employee_id
        )
        if not is_valid:
            return jsonify({'error': policy_err}), 400
            
        # Check history
        is_reused, history_err = AuthUtils.check_password_history(employee_id, new_password)
        if is_reused:
            return jsonify({'error': history_err}), 400
            
        # Update password
        new_hash = AuthUtils.hash_password(new_password)
        SupabaseDB.update('employees',
                         {'employee_id': employee_id},
                         {
                             'password_hash': new_hash,
                             'password_changed_at': datetime.now(timezone.utc).isoformat(),
                             'failed_login_attempts': 0,
                             'lockout_until': None
                         })
                         
        # Add to history
        try:
            SupabaseDB.insert('password_history', {
                'employee_id': employee_id,
                'password_hash': new_hash,
                'created_at': datetime.now(timezone.utc).isoformat()
            })
        except Exception as he:
            logger.error(f"Failed to insert password history: {he}")
            
        # Generate full tokens to log them in directly
        access_token = AuthUtils.create_access_token(employee['employee_id'], employee['role'])
        refresh_token = AuthUtils.create_refresh_token(employee['employee_id'], employee['role'])
        
        log_audit(employee_id, 'PASSWORD_RESET_EXPIRED', 'employee')
        
        return jsonify({
            'message': 'Password reset successfully. Logged in.',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'employee': {
                'employee_id': employee['employee_id'],
                'email': employee['email'],
                'full_name': employee['full_name'],
                'role': employee['role'],
                'designation': employee['designation']
            }
        }), 200
    except Exception as e:
        logger.error(f"Reset expired password error: {str(e)}")
        return jsonify({'error': 'Failed to reset password'}), 500


@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Missing refresh token'}), 400
        
        payload = AuthUtils.verify_token(refresh_token, expected_type='refresh')
        
        # Create new access token
        new_access_token = AuthUtils.create_access_token(
            payload['employee_id'],
            payload['role']
        )
        
        return jsonify({
            'access_token': new_access_token
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 401


@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset link to registered OTSi email"""
    try:
        data = request.get_json()
        email = (data.get('email') or '').strip().lower()

        if not email:
            return jsonify({'error': 'Email address is required'}), 400

        # Validate domain — only allowed OTSi domains
        valid_domains = ['otsi-usa.com', 'otsi.co.in']
        if not any(email.endswith(f'@{domain}') for domain in valid_domains):
            return jsonify({'error': 'Only @otsi-usa.com or @otsi.co.in addresses are accepted'}), 400

        # Validate name.surname format
        local_part = email.split('@')[0]
        if '.' not in local_part or local_part.startswith('.') or local_part.endswith('.'):
            return jsonify({'error': 'Email must follow format name.surname@otsi-usa.com'}), 400

        # Check if email is registered
        employee = SupabaseDB.select_one('employees', {'email': email})
        if not employee:
            return jsonify({'error': 'No employee found with this email address.'}), 404
            
        # Generate a short-lived reset token (1 hour)
        reset_token = AuthUtils.create_access_token(employee['employee_id'], 'reset', expires_in=1)
        
        # Record audit log
        log_audit(employee['employee_id'], 'FORGOT_PASSWORD', 'auth')
        logger.info(f"Password reset requested for {email}")
        
        # Print the reset link to the console for local development testing
        reset_link = f"http://127.0.0.1:5000/?reset_token={reset_token}&emp_id={employee['employee_id']}"
        
        # Send the real email asynchronously to prevent UI delay
        from threading import Thread
        Thread(target=EmailService.send_password_reset_email, args=(email, reset_link)).start()
        
        # Since email is async, we can't reliably fallback immediately to console,
        # but we can just print the mock link to the console for dev testing regardless.
        print("\n" + "="*60)
        print("[MOCK EMAIL NOTIFICATION (OR BACKUP DEV LINK)]")
        print(f"To: {email}")
        print(f"Subject: OTSi ESS Portal - Password Reset")
        print(f"Click the link below to reset your password:")
        print(f"{reset_link}")
        print("="*60 + "\n")

        return jsonify({
            'message': 'A password reset link has been sent to your email.'
        }), 200

    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return jsonify({'error': 'Request failed. Please try again.'}), 500


@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password using email token"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        temp_token = data.get('temp_token')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if not all([employee_id, temp_token, new_password, confirm_password]):
            return jsonify({'error': 'Missing required fields'}), 400

        if new_password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400

        employee = SupabaseDB.select_one('employees', {'employee_id': employee_id})
        if not employee:
            return jsonify({'error': 'Invalid request'}), 400

        # Validate token statelessly via JWT
        try:
            payload = AuthUtils.verify_token(temp_token)
            if payload.get('role') != 'reset' or payload.get('employee_id') != employee_id:
                return jsonify({'error': 'Invalid reset token'}), 400
                
            # Verify that password wasn't already changed after this token was issued
            if employee.get('password_changed_at'):
                pwd_changed_val = employee.get('password_changed_at')
                pwd_changed: datetime | None = None
                if isinstance(pwd_changed_val, str):
                    pwd_changed = datetime.fromisoformat(pwd_changed_val.replace('Z', '+00:00'))
                elif isinstance(pwd_changed_val, datetime):
                    pwd_changed = pwd_changed_val
                
                if pwd_changed is not None:
                    if pwd_changed.tzinfo is None:
                        pwd_changed = pwd_changed.replace(tzinfo=timezone.utc)
                    else:
                        pwd_changed = pwd_changed.astimezone(timezone.utc)

                    # Token iat is Unix timestamp. Convert to timezone-aware UTC datetime.
                    token_issued = datetime.fromtimestamp(payload.get('iat', 0), timezone.utc)
                    if pwd_changed > token_issued:
                        return jsonify({'error': 'This reset link has already been used.'}), 400
        except Exception as e:
            return jsonify({'error': 'Invalid or expired reset token'}), 400

        # Validate policy
        is_valid, msg = AuthUtils.validate_password_policy(
            new_password, employee.get('email', ''), employee.get('full_name', ''), employee_id
        )
        if not is_valid:
            return jsonify({'error': msg}), 400

        # Check history
        is_reused, msg = AuthUtils.check_password_history(employee_id, new_password)
        if is_reused:
            return jsonify({'error': msg}), 400

        # Update password
        new_hash = AuthUtils.hash_password(new_password)
        SupabaseDB.update('employees',
                          {'employee_id': employee_id},
                          {
                              'password_hash': new_hash,
                              'password_changed_at': datetime.now(timezone.utc).isoformat()
                          })

        SupabaseDB.insert('password_history', {
            'employee_id': employee_id,
            'password_hash': new_hash
        })
        
        log_audit(employee_id, 'PASSWORD_RESET', 'auth')

        # Clear active sessions (if table exists)
        try:
            SupabaseDB.delete('sessions', {'employee_id': employee_id})
        except Exception as se:
            logger.warning(f"Could not delete sessions: {se}")

        return jsonify({'message': 'Password successfully reset'}), 200

    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        return jsonify({'error': 'Request failed'}), 500


# ═════════════════════════════════════════════════════════════
# ATTENDANCE ENDPOINTS
# ═════════════════════════════════════════════════════════════

@app.route('/api/attendance/check-in', methods=['POST'])
@token_required
def check_in():
    """Check in for attendance"""
    try:
        data = request.get_json()
        employee_id = g.current_employee_id
        
        today = date.today()
        check_in_time = datetime.now(timezone.utc)
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        is_wfh = data.get('is_wfh', False)
        
        # Check if already checked in today
        existing = SupabaseDB.select_one('attendance_logs', {
            'employee_id': employee_id,
            'attendance_date': today.isoformat()
        })
        
        if existing and existing['check_in_time']:
            return jsonify({'error': 'Already checked in today'}), 400
        
        # Verify location if not WFH
        location_verified = is_wfh
        location_info = None
        
        if not is_wfh and latitude and longitude:
            from config import Config
            office_locs = getattr(Config, 'OFFICE_LOCATIONS', None)
            is_allowed = LocationUtils.is_within_office(
                latitude, longitude,
                Config.OFFICE_LAT, Config.OFFICE_LNG,
                Config.OFFICE_RADIUS_M,
                office_locations=office_locs,
                metro_radius_m=getattr(Config, 'OFFICE_METRO_RADIUS_M', 20000)
            )
            if not is_allowed:
                min_dist = float('inf')
                locs_to_check = office_locs if office_locs else [{'lat': Config.OFFICE_LAT, 'lng': Config.OFFICE_LNG}]
                for loc in locs_to_check:
                    d = LocationUtils.calculate_distance(latitude, longitude, loc['lat'], loc['lng'])
                    if d < min_dist:
                        min_dist = d
                km = round(min_dist / 1000.0, 1)
                return jsonify({
                    'error': f'Check-in denied: You are outside the OTSi office geofence ({km} km away). Connect to office Wi-Fi, disable VPN, or enable WFH mode.',
                    'distance_km': km
                }), 403
            location_verified = True
            location_info = f"{latitude},{longitude}"
        elif not is_wfh and not latitude:
            return jsonify({'error': 'Check-in denied: Location is required for office check-in.'}), 400
        
        # Determine status (IST: UTC + 5:30)
        ist_time = check_in_time + timedelta(hours=5, minutes=30)
        late_threshold = datetime.strptime("09:30", "%H:%M").time()
        status = 'wfh' if is_wfh else (
            'late' if ist_time.time() > late_threshold else 'present'
        )
        
        # Create or update attendance record
        if existing:
            # Update existing record
            SupabaseDB.update('attendance_logs',
                             {'employee_id': employee_id, 'attendance_date': today.isoformat()},
                             {
                                 'check_in_time': check_in_time.isoformat(),
                                 'check_in_latitude': latitude,
                                 'check_in_longitude': longitude,
                                 'check_in_location': location_info,
                                 'is_wfh': is_wfh,
                                 'status': status,
                                 'location_verified': location_verified,
                                 'is_late': status == 'late'
                             })
            attendance_id = existing['id']
        else:
            # Create new record
            attendance_data = {
                'employee_id': employee_id,
                'attendance_date': today.isoformat(),
                'check_in_time': check_in_time.isoformat(),
                'check_in_latitude': latitude,
                'check_in_longitude': longitude,
                'check_in_location': location_info,
                'is_wfh': is_wfh,
                'status': status,
                'location_verified': location_verified,
                'is_late': status == 'late'
            }
            attendance = SupabaseDB.insert('attendance_logs', attendance_data)
            attendance_id = attendance['id'] if attendance else None
        
        # Create notification (convert UTC to IST = UTC + 5:30)
        ist_check_in = check_in_time + timedelta(hours=5, minutes=30)
        NotificationUtils.create_notification(
            employee_id,
            'Check In Successful',
            f'Checked in at {ist_check_in.strftime("%I:%M %p")} IST ({status.upper()})',
            'checkin',
            action_url='att'
        )
        
        log_audit(employee_id, 'CHECK_IN', 'attendance', attendance_id)
        
        return jsonify({
            'message': 'Checked in successfully',
            'check_in_time': check_in_time.isoformat(),
            'status': status,
            'location_verified': location_verified
        }), 200
        
    except Exception as e:
        logger.error(f"Check-in error: {str(e)}")
        return jsonify({'error': 'Check-in failed'}), 500


@app.route('/api/attendance/check-out', methods=['POST'])
@token_required
def check_out():
    """Check out from attendance"""
    try:
        employee_id = g.current_employee_id
        today = date.today()
        check_out_time = datetime.now(timezone.utc)
        
        data = request.get_json(silent=True) or {}
        is_wfh = data.get('is_wfh', False)
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # Verify location if not WFH
        if not is_wfh and latitude and longitude:
            from config import Config
            office_locs = getattr(Config, 'OFFICE_LOCATIONS', None)
            is_allowed = LocationUtils.is_within_office(
                latitude, longitude,
                Config.OFFICE_LAT, Config.OFFICE_LNG,
                Config.OFFICE_RADIUS_M,
                office_locations=office_locs,
                metro_radius_m=getattr(Config, 'OFFICE_METRO_RADIUS_M', 20000)
            )
            if not is_allowed:
                min_dist = float('inf')
                locs_to_check = office_locs if office_locs else [{'lat': Config.OFFICE_LAT, 'lng': Config.OFFICE_LNG}]
                for loc in locs_to_check:
                    d = LocationUtils.calculate_distance(latitude, longitude, loc['lat'], loc['lng'])
                    if d < min_dist:
                        min_dist = d
                km = round(min_dist / 1000.0, 1)
                return jsonify({
                    'error': f'Check-out denied: You are outside office premises ({km} km away). Please enable WFH mode to check out remotely.',
                    'distance_km': km
                }), 403
        
        # Get today's attendance record
        record = SupabaseDB.select_one('attendance_logs', {
            'employee_id': employee_id,
            'attendance_date': today.isoformat()
        })
        
        if not record or not record['check_in_time']:
            return jsonify({'error': 'Not checked in today'}), 400
        
        # Calculate working hours
        check_in = datetime.fromisoformat(record['check_in_time'])
        working_hours = AttendanceUtils.calculate_working_hours(check_in, check_out_time)
        
        # Apply 7-hour minimum rule for full day
        new_status = record['status']
        if working_hours < 7.0 and new_status not in ['absent']:
            new_status = 'half_day'
        elif not is_wfh and new_status == 'wfh':
            # Checked in WFH, but checked out from Office premises -> Hybrid day, marked present
            new_status = 'present'
            
        # Update record
        SupabaseDB.update('attendance_logs',
                         {'employee_id': employee_id, 'attendance_date': today.isoformat()},
                         {
                             'check_out_time': check_out_time.isoformat(),
                             'working_hours': working_hours,
                             'status': new_status
                         })
        
        # Create notification (convert UTC to IST = UTC + 5:30)
        ist_check_out = check_out_time + timedelta(hours=5, minutes=30)
        mode_label = 'WFH' if is_wfh else 'Office'
        NotificationUtils.create_notification(
            employee_id,
            'Check Out Successful',
            f'Checked out at {ist_check_out.strftime("%I:%M %p")} IST ({mode_label}) - Worked {working_hours:.2f} hours',
            'checkout',
            action_url='att'
        )
        
        log_audit(employee_id, 'CHECK_OUT', 'attendance', record['id'])
        
        return jsonify({
            'message': 'Checked out successfully',
            'check_out_time': check_out_time.isoformat(),
            'working_hours': working_hours,
            'is_wfh': is_wfh,
            'status': new_status
        }), 200
        
    except Exception as e:
        logger.error(f"Check-out error: {str(e)}")
        return jsonify({'error': 'Check-out failed'}), 500


@app.route('/api/attendance/today', methods=['GET'])
@token_required
def get_today_attendance():
    """Get today's attendance for current employee"""
    try:
        employee_id = g.current_employee_id
        today = date.today()
        
        record = SupabaseDB.select_one('attendance_logs', {
            'employee_id': employee_id,
            'attendance_date': today.isoformat()
        })
        
        if not record:
            return jsonify({
                'status': 'absent',
                'check_in_time': None,
                'check_out_time': None,
                'working_hours': 0
            }), 200
        
        return jsonify({
            'id': record['id'],
            'status': record['status'],
            'check_in_time': record['check_in_time'],
            'check_out_time': record['check_out_time'],
            'working_hours': record['working_hours'],
            'is_wfh': record['is_wfh'],
            'is_late': record['is_late'],
            'check_in_location': record.get('check_in_location')
        }), 200
        
    except Exception as e:
        logger.error(f"Get today attendance error: {str(e)}")
        return jsonify({'error': 'Failed to fetch attendance'}), 500


@app.route('/api/attendance/history', methods=['GET'])
@token_required
def get_attendance_history():
    """Get attendance history for employee"""
    try:
        employee_id = g.current_employee_id
        days = request.args.get('days', 30, type=int)
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        
        if month and year:
            import calendar
            _, last_day = calendar.monthrange(year, month)
            start_dt = date(year, month, 1)
            end_dt = min(date(year, month, last_day), date.today())
            
            # Fetch all logs for employee
            all_records = SupabaseDB.select('attendance_logs', '*', {'employee_id': employee_id})
            # Filter in python
            records = [r for r in all_records if start_dt.isoformat() <= r['attendance_date'] <= end_dt.isoformat()]
            
            records = AttendanceUtils.fill_missing_attendance(employee_id, records, start_dt, end_dt)
        else:
            start_date = date.today() - timedelta(days=days)
            end_date = date.today()
            db_records = SupabaseDB.select('attendance_logs',
                                       '*',
                                       {
                                           'employee_id': employee_id,
                                           'attendance_date': ('gte', start_date.isoformat())
                                       })
            records = AttendanceUtils.fill_missing_attendance(employee_id, db_records, start_date, end_date)
        
        # Sort by date descending
        records.sort(key=lambda x: x['attendance_date'], reverse=True)
        
        return jsonify({'attendance_logs': records, 'count': len(records)}), 200
        
    except Exception as e:
        logger.error(f"Get attendance history error: {str(e)}")
        return jsonify({'error': 'Failed to fetch attendance history'}), 500


@app.route('/api/attendance/stats', methods=['GET'])
@token_required
def get_attendance_stats():
    """Get attendance statistics"""
    try:
        employee_id = g.current_employee_id
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        stats = AttendanceUtils.get_attendance_stats(employee_id, month, year)
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Get attendance stats error: {str(e)}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500


# ═════════════════════════════════════════════════════════════
# LEAVE ENDPOINTS
# ═════════════════════════════════════════════════════════════

@app.route('/api/leave/balance', methods=['GET'])
@token_required
def get_leave_balance():
    """Get leave balance"""
    try:
        employee_id = g.current_employee_id
        balance = LeaveUtils.get_leave_balance(employee_id)
        
        return jsonify(balance), 200
        
    except Exception as e:
        logger.error(f"Get leave balance error: {str(e)}")
        return jsonify({'error': 'Failed to fetch leave balance'}), 500


@app.route('/api/leave/apply', methods=['POST'])
@token_required
def apply_leave():
    """Apply for leave"""
    try:
        data = request.get_json()
        employee_id = g.current_employee_id
        
        required = ['leave_type', 'start_date', 'end_date', 'reason']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        leave_type = data['leave_type']
        start_date = date.fromisoformat(data['start_date'])
        end_date = date.fromisoformat(data['end_date'])
        reason = data['reason']
        
        # Calculate number of days
        num_days = LeaveUtils.calculate_leave_days(start_date, end_date)
        
        # Leave types that don't consume a numeric balance (permission-style)
        non_balance_types = {'permission', 'wfh', 'half_day', 'paternity', 'optional_holiday'}
        
        # Check balance only for types that have a tracked balance column
        if leave_type not in non_balance_types:
            leave_column = LeaveUtils.get_leave_column(leave_type)
            if leave_column is None:
                return jsonify({'error': f'Invalid leave type: {leave_type}'}), 400
        
        # Create leave application
        leave_data = {
            'employee_id': employee_id,
            'leave_type': leave_type,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'number_of_days': num_days,
            'reason': reason,
            'status': 'pending',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        leave_app = SupabaseDB.insert('leave_applications', leave_data)
        
        # Create notification for HR and Manager
        # Find the employee's manager
        employee_details = SupabaseDB.select_one('employees', {'employee_id': employee_id})
        manager_id = employee_details.get('manager_id') if employee_details else None

        # Find all HRs
        hr_users = SupabaseDB.select('employees', 'employee_id', {'role': 'hr'})
        admin_users = SupabaseDB.select('employees', 'employee_id', {'role': 'admin'})
        hr_ids = [u['employee_id'] for u in hr_users + admin_users]
        
        notify_ids = set(hr_ids)
        if manager_id:
            notify_ids.add(manager_id)
            
        employee_name = (employee_details.get('full_name') if employee_details else None) or employee_id

        for nid in notify_ids:
            NotificationUtils.create_notification(
                nid,
                'Leave Application',
                f'{employee_name} has applied for {leave_type} leave from {start_date} to {end_date}',
                'leave_approval',
                action_url=f'leave_approval:{leave_app["id"]}' if leave_app else 'leave_approval'
            )
        
        log_audit(employee_id, 'APPLY_LEAVE', 'leave_applications', 
                 new_values=leave_data)
        
        return jsonify({
            'message': 'Leave application submitted',
            'application_id': leave_app['id'] if leave_app else None
        }), 201
        
    except Exception as e:
        logger.error(f"Apply leave error: {str(e)}")
        return jsonify({'error': 'Failed to apply leave'}), 500


@app.route('/api/leave/history', methods=['GET'])
@token_required
def get_leave_history():
    """Get leave application history"""
    try:
        employee_id = g.current_employee_id
        
        records = SupabaseDB.select('leave_applications', '*',
                                   {'employee_id': employee_id})
        
        # Sort by date descending
        records.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Ensure approval_date and approved_by fields are always present
        for rec in records:
            if 'approval_date' not in rec:
                rec['approval_date'] = rec.get('updated_at') if rec.get('status') != 'pending' else None
            if 'approved_by' not in rec:
                rec['approved_by'] = rec.get('reviewer_name') or rec.get('approved_by_name') or ''
        
        return jsonify({'leave_applications': records}), 200
        
    except Exception as e:
        logger.error(f"Get leave history error: {str(e)}")
        return jsonify({'error': 'Failed to fetch leave history'}), 500


# ═════════════════════════════════════════════════════════════
# TIMESHEET ENDPOINTS
# ═════════════════════════════════════════════════════════════

@app.route('/api/timesheet', methods=['GET'])
@token_required
def get_timesheet():
    """Get timesheet and its entries for a week"""
    try:
        employee_id = g.current_employee_id
        week_start_str = request.args.get('week_start_date')
        
        if not week_start_str:
            # Default to current week's Monday
            start_date, _ = TimesheetUtils.get_week_dates()
            week_start_str = start_date.isoformat()
        
        timesheet = SupabaseDB.select_one('timesheets', {
            'employee_id': employee_id,
            'week_start_date': week_start_str
        })
        
        if not timesheet:
            return jsonify({
                'timesheet': None,
                'entries': []
            }), 200
            
        entries = SupabaseDB.select('timesheet_entries', '*', {
            'timesheet_id': timesheet['id']
        })
        
        # Sort entries by date ascending
        entries.sort(key=lambda x: x['entry_date'])
        
        return jsonify({
            'timesheet': timesheet,
            'entries': entries
        }), 200
        
    except Exception as e:
        logger.error(f"Get timesheet error: {str(e)}")
        return jsonify({'error': 'Failed to fetch timesheet'}), 500


@app.route('/api/timesheet/history', methods=['GET'])
@token_required
def get_timesheet_history():
    """Get all timesheets for current employee"""
    try:
        employee_id = g.current_employee_id
        
        records = SupabaseDB.select('timesheets', '*', {
            'employee_id': employee_id
        })
        
        # Sort by week start date descending
        records.sort(key=lambda x: x['week_start_date'], reverse=True)
        
        return jsonify({'timesheets': records, 'count': len(records)}), 200
        
    except Exception as e:
        logger.error(f"Get timesheet history error: {str(e)}")
        return jsonify({'error': 'Failed to fetch timesheet history'}), 500


@app.route('/api/timesheet/create', methods=['POST'])
@token_required
def create_timesheet():
    """Create timesheet for week"""
    try:
        data = request.get_json()
        employee_id = g.current_employee_id
        
        week_start = date.fromisoformat(data.get('week_start_date'))
        week_end = date.fromisoformat(data.get('week_end_date'))
        
        # Check if timesheet already exists
        existing = SupabaseDB.select_one('timesheets', {
            'employee_id': employee_id,
            'week_start_date': week_start.isoformat()
        })
        
        if existing:
            return jsonify({'error': 'Timesheet already exists for this week'}), 400
        
        # Create timesheet
        timesheet_data = {
            'employee_id': employee_id,
            'week_start_date': week_start.isoformat(),
            'week_end_date': week_end.isoformat(),
            'status': 'draft',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        timesheet = SupabaseDB.insert('timesheets', timesheet_data)
        
        log_audit(employee_id, 'CREATE_TIMESHEET', 'timesheets',
                 new_values=timesheet_data)
        
        return jsonify({
            'message': 'Timesheet created',
            'timesheet_id': timesheet['id'] if timesheet else None
        }), 201
        
    except Exception as e:
        logger.error(f"Create timesheet error: {str(e)}")
        return jsonify({'error': 'Failed to create timesheet'}), 500


@app.route('/api/timesheet/<int:timesheet_id>/add-entry', methods=['POST'])
@token_required
def add_timesheet_entry(timesheet_id):
    """Add entry to timesheet"""
    try:
        data = request.get_json()
        employee_id = g.current_employee_id
        
        # Verify ownership
        timesheet = SupabaseDB.select_one('timesheets', {'id': timesheet_id})
        if not timesheet or timesheet['employee_id'] != employee_id:
            return jsonify({'error': 'Timesheet not found or access denied'}), 404
        
        entry_data = {
            'timesheet_id': timesheet_id,
            'entry_date': data['entry_date'],
            'project_name': data.get('project_name'),
            'task_description': data.get('task_description'),
            'hours_worked': data['hours_worked'],
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        entry = SupabaseDB.insert('timesheet_entries', entry_data)
        
        # Update timesheet total hours
        total_hours = TimesheetUtils.calculate_timesheet_hours(timesheet_id)
        SupabaseDB.update('timesheets', {'id': timesheet_id}, {'total_hours': total_hours})
        
        log_audit(employee_id, 'ADD_TIMESHEET_ENTRY', 'timesheet_entries',
                 new_values=entry_data)
        
        entry_id = entry['id'] if entry else None
        return jsonify({'message': 'Entry added', 'entry_id': entry_id}), 201
        
    except Exception as e:
        logger.error(f"Add timesheet entry error: {str(e)}")
        return jsonify({'error': 'Failed to add entry'}), 500


@app.route('/api/timesheet/<int:timesheet_id>/entries', methods=['DELETE'])
@token_required
def delete_timesheet_entries(timesheet_id):
    """Delete all entries for a timesheet (draft only)"""
    try:
        employee_id = g.current_employee_id
        
        # Verify ownership
        timesheet = SupabaseDB.select_one('timesheets', {'id': timesheet_id})
        if not timesheet or timesheet['employee_id'] != employee_id:
            return jsonify({'error': 'Timesheet not found'}), 404
            
        if timesheet['status'] != 'draft':
            return jsonify({'error': 'Cannot modify a submitted timesheet'}), 400
            
        # Delete entries
        SupabaseDB.delete('timesheet_entries', {'timesheet_id': timesheet_id})
        
        # Reset total hours
        SupabaseDB.update('timesheets', {'id': timesheet_id}, {'total_hours': 0})
        
        return jsonify({'message': 'Entries cleared'}), 200
        
    except Exception as e:
        logger.error(f"Delete entries error: {str(e)}")
        return jsonify({'error': 'Failed to clear entries'}), 500


@app.route('/api/timesheet/<int:timesheet_id>/submit', methods=['POST'])
@token_required
def submit_timesheet(timesheet_id):
    """Submit timesheet for approval"""
    try:
        employee_id = g.current_employee_id
        
        timesheet = SupabaseDB.select_one('timesheets', {'id': timesheet_id})
        if not timesheet or timesheet['employee_id'] != employee_id:
            return jsonify({'error': 'Timesheet not found'}), 404
        
        # Update status
        SupabaseDB.update('timesheets', {'id': timesheet_id},
                         {
                             'status': 'submitted',
                             'submitted_date': datetime.now(timezone.utc).isoformat()
                         })
        
        # Create notification for manager
        manager_id = 'EMP2001'  # Default to HR Manager
        NotificationUtils.create_notification(
            manager_id,
            'Timesheet Submission',
            f'Timesheet submitted by {employee_id} for week {timesheet["week_start_date"]}',
            'timesheet_approval',
            action_url='ts'
        )
        
        log_audit(employee_id, 'SUBMIT_TIMESHEET', 'timesheets')
        
        return jsonify({'message': 'Timesheet submitted'}), 200
        
    except Exception as e:
        logger.error(f"Submit timesheet error: {str(e)}")
        return jsonify({'error': 'Failed to submit timesheet'}), 500


# ═════════════════════════════════════════════════════════════
# HELP DESK ENDPOINTS
# ═════════════════════════════════════════════════════════════

@app.route('/api/tickets/create', methods=['POST'])
@token_required
def create_ticket():
    """Create IT support ticket"""
    try:
        data = request.get_json()
        employee_id = g.current_employee_id
        
        required = ['category', 'priority', 'subject', 'description']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Generate ticket number
        import random
        ticket_number = f"HD-{datetime.now().year}-{random.randint(1000, 9999)}"
        
        ticket_data = {
            'ticket_number': ticket_number,
            'employee_id': employee_id,
            'category': data['category'],
            'priority': data['priority'],
            'subject': data['subject'],
            'description': data['description'],
            'status': 'open',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        ticket = SupabaseDB.insert('support_tickets', ticket_data)
        
        # Create notification for IT team / Admin
        try:
            admin_users = SupabaseDB.select('employees', 'employee_id', {'role': 'admin'})
            notify_target = admin_users[0]['employee_id'] if admin_users else 'EMP1000'
            NotificationUtils.create_notification(
                notify_target,
                'New Support Ticket',
                f'New {data["priority"]} ticket: {data["subject"]}',
                'ticket_alert',
                action_url='hd'
            )
        except Exception as notif_err:
            logger.error(f"Ticket notification warning: {notif_err}")
        
        log_audit(employee_id, 'CREATE_TICKET', 'support_tickets',
                 new_values=ticket_data)
        
        return jsonify({
            'message': 'Ticket created',
            'ticket_number': ticket_number
        }), 201
        
    except Exception as e:
        logger.error(f"Create ticket error: {str(e)}")
        return jsonify({'error': 'Failed to create ticket'}), 500


@app.route('/api/tickets', methods=['GET'])
@token_required
def get_tickets():
    """Get support tickets"""
    try:
        employee_id = g.current_employee_id
        
        if g.current_role == 'admin':
            # Admin sees all tickets
            tickets = SupabaseDB.select('support_tickets', '*')
        else:
            # Employee sees only their tickets
            tickets = SupabaseDB.select('support_tickets', '*',
                                       {'employee_id': employee_id})
        
        # Sort by date descending
        tickets.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({'tickets': tickets, 'count': len(tickets)}), 200
        
    except Exception as e:
        logger.error(f"Get tickets error: {str(e)}")
        return jsonify({'error': 'Failed to fetch tickets'}), 500


# ═════════════════════════════════════════════════════════════
# EMPLOYEE PROFILE ENDPOINTS
# ═════════════════════════════════════════════════════════════

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile():
    """Get employee profile"""
    try:
        employee_id = g.current_employee_id
        
        employee = SupabaseDB.select_one('employees', {'employee_id': employee_id})
        
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Remove sensitive data
        employee.pop('password_hash', None)
        
        # Check if they have reportees
        reports = SupabaseDB.select('employees', 'employee_id', {'manager_id': employee_id})
        employee['is_manager'] = len(reports) > 0
        employee['is_system_admin'] = is_system_admin_account(employee)
        
        employee['mfa_globally_enabled'] = is_mfa_enabled_globally()

        # Attach an HRBP
        hr_users = SupabaseDB.select('employees', 'full_name', {'role': 'hr', 'team': 'HRBP'})
        if not hr_users:
            hr_users = SupabaseDB.select('employees', 'full_name', {'role': 'hr'})
            
        if hr_users:
            # Simple hash to consistently assign the same HRBP to the same employee
            idx = hash(employee_id) % len(hr_users)
            employee['hrbp_name'] = hr_users[idx]['full_name']
        else:
            employee['hrbp_name'] = 'Global HR Team'
            
        return jsonify(employee), 200
        
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return jsonify({'error': 'Failed to fetch profile'}), 500


@app.route('/api/profile/update', methods=['PUT'])
@token_required
def update_profile():
    """Update employee profile"""
    try:
        data = request.get_json()
        employee_id = g.current_employee_id
        
        # Only allow updating certain fields
        allowed_fields = ['phone', 'designation', 'department']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        SupabaseDB.update('employees', {'employee_id': employee_id}, update_data)
        
        log_audit(employee_id, 'UPDATE_PROFILE', 'employees',
                 new_values=update_data)
        
        return jsonify({'message': 'Profile updated'}), 200
        
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500


@app.route('/api/org-tree', methods=['GET'])
@token_required
def get_org_tree():
    """Build and return dynamic multi-level org hierarchy tree with Team/Department Scoping"""
    try:
        req_emp_id = (request.args.get('emp_id') or '').strip().upper()
        target_emp_id = req_emp_id if req_emp_id else g.current_employee_id
        
        target_emp = SupabaseDB.select_one('employees', {'employee_id': target_emp_id})
        scope = (request.args.get('scope') or 'team').strip().lower()

        employees = SupabaseDB.select('employees', '*')
        active_emps = [e for e in employees if classify_employee_record(e) == 'active']
        
        # Build map of employee_id -> node object
        emp_map = {}
        for emp in active_emps:
            emp_id = emp['employee_id']
            name_parts = (emp.get('full_name') or '').split()
            initials = ''.join([part[0] for part in name_parts if part]).upper()[:2] or 'EM'
            emp_map[emp_id] = {
                'id': f"node-{emp_id.lower()}",
                'employee_id': emp_id,
                'name': emp.get('full_name') or emp_id,
                'initials': initials,
                'role': emp.get('designation') or emp.get('role', '').upper() or 'Employee',
                'department': emp.get('department') or 'Engineering',
                'manager_id': emp.get('manager_id'),
                'raw_role': emp.get('role', 'employee'),
                'children': []
            }

        # Connect children to parent managers dynamically
        full_roots = []
        for emp_id, node in emp_map.items():
            mgr_id = node.get('manager_id')
            if mgr_id and mgr_id in emp_map and mgr_id != emp_id:
                emp_map[mgr_id]['children'].append(node)
            else:
                full_roots.append(node)

        # Build personal reporting chain for target employee (Top Exec -> Manager -> Target Employee)
        chain = []
        curr = emp_map.get(target_emp_id)
        visited = set()
        while curr and curr['employee_id'] not in visited:
            visited.add(curr['employee_id'])
            chain.insert(0, {
                'employee_id': curr['employee_id'],
                'name': curr['name'],
                'initials': curr['initials'],
                'role': curr['role'],
                'department': curr['department'],
                'raw_role': curr.get('raw_role', 'employee'),
                'isMe': curr['employee_id'] == target_emp_id
            })
            mgr_id = curr.get('manager_id')
            if mgr_id and mgr_id in emp_map and mgr_id != curr['employee_id']:
                curr = emp_map[mgr_id]
            else:
                break

        # Team Scoped Tree vs Company Tree
        if scope == 'team' and target_emp:
            # Find the root node of the target employee's hierarchy branch
            root_node = emp_map.get(target_emp_id)
            if root_node:
                p_id = root_node.get('manager_id')
                p_visited = set([root_node['employee_id']])
                while p_id and p_id in emp_map and p_id not in p_visited:
                    p_visited.add(p_id)
                    root_node = emp_map[p_id]
                    p_id = root_node.get('manager_id')
                tree_output = [root_node]
            else:
                tree_output = full_roots
        else:
            tree_output = full_roots

        return jsonify({
            'tree': tree_output,
            'chain': chain,
            'scope': scope,
            'target_employee_id': target_emp_id,
            'total_active': len(active_emps)
        }), 200

    except Exception as e:
        logger.error(f"Get org tree error: {str(e)}")
        return jsonify({'error': 'Failed to build dynamic org tree'}), 500


# ═════════════════════════════════════════════════════════════
# HR/ADMIN ENDPOINTS
# ═════════════════════════════════════════════════════════════

@app.route('/api/admin/employees', methods=['GET'])
@token_required
def get_all_employees():
    """Get employees (HR/Admin sees all, Managers see their reportees)."""
    try:
        current_emp_id = g.current_employee_id
        _, is_hr, is_manager, reports, _ = get_scope_context(current_emp_id)

        if not (is_hr or is_manager):
            return jsonify({'error': 'Unauthorized'}), 403

        employees = SupabaseDB.select('employees', '*') if is_hr else reports
        status_filter = (request.args.get('status') or '').strip().lower()
        if status_filter:
            employees = [emp for emp in employees if classify_employee_record(emp) == status_filter]

        employees.sort(key=lambda e: (e.get('full_name') or '').lower())

        summary = {
            'total': len(employees),
            'active': len([e for e in employees if classify_employee_record(e) == 'active']),
            'inactive': len([e for e in employees if classify_employee_record(e) == 'inactive']),
            'pending': len([e for e in employees if classify_employee_record(e) == 'pending'])
        }

        for emp in employees:
            emp.pop('password_hash', None)
            emp['record_status'] = classify_employee_record(emp)

        return jsonify({'employees': employees, 'count': len(employees), 'summary': summary}), 200

    except Exception as e:
        logger.error(f"Get employees error: {str(e)}")
        return jsonify({'error': 'Failed to fetch employees'}), 500


@app.route('/api/admin/employees/<employee_id>/status', methods=['POST'])
@token_required
@role_required('hr', 'admin')
def update_employee_status(employee_id):
    """Update employee account status (active, inactive)"""
    try:
        data = request.get_json() or {}
        new_status = data.get('status')
        if new_status not in ['active', 'inactive']:
            return jsonify({'error': 'Invalid status'}), 400
            
        # Get target employee details
        emp = SupabaseDB.select_one('employees', {'employee_id': employee_id})
        if not emp:
            return jsonify({'error': 'Employee not found'}), 404
            
        if new_status == 'inactive':
            # Check if this is a pending registration (no manager or designation details)
            if not emp.get('manager_id') and not emp.get('designation'):
                # Hard reject: delete the fake/pending record entirely from the db
                SupabaseDB.delete('employees', {'employee_id': employee_id})
                log_audit(g.current_employee_id, 'REJECT_PENDING_REGISTRATION', 'employees', 
                          entity_id=employee_id, new_values={})
                return jsonify({'message': 'Pending registration rejected and removed.'}), 200
        
        # Otherwise, update status (activate or deactivate)
        SupabaseDB.update('employees', {'employee_id': employee_id}, {'status': new_status})
        log_audit(g.current_employee_id, 'UPDATE_EMPLOYEE_STATUS', 'employees', 
                  entity_id=employee_id, new_values={'status': new_status})
                  
        return jsonify({'message': f'Employee status updated to {new_status}'}), 200
    except Exception as e:
        logger.error(f"Update employee status error: {str(e)}")
        return jsonify({'error': 'Failed to update status'}), 500


@app.route('/api/admin/team-attendance', methods=['GET'])
@token_required
def get_team_attendance():
    """Get team attendance for today (HR/Admin gets all, Managers get reportees)"""
    try:
        current_emp_id = g.current_employee_id
        current_emp = SupabaseDB.select_one('employees', {'employee_id': current_emp_id})
        
        is_hr = current_emp and current_emp.get('role') in ['hr', 'admin']
        
        # Check if they have reportees
        reports = SupabaseDB.select('employees', 'employee_id', {'manager_id': current_emp_id})
        report_ids = [r['employee_id'] for r in reports]
        is_manager = len(report_ids) > 0
        
        if not (is_hr or is_manager):
            return jsonify({'error': 'Unauthorized'}), 403
            
        today = date.today()
        
        attendance = SupabaseDB.select('attendance_logs', '*',
                                      {'attendance_date': today.isoformat()})
        
        # Filter if not HR
        if not is_hr:
            attendance = [a for a in attendance if a['employee_id'] in report_ids]
            
        # Batch lookup all employees to avoid 257 individual queries
        all_emps = {e['employee_id']: e for e in SupabaseDB.select('employees', '*')}
        result = []
        for att in attendance:
            emp = all_emps.get(att['employee_id'])
            if emp:
                result.append({
                    'employee_id': emp['employee_id'],
                    'name': emp['full_name'],
                    'designation': emp.get('designation', 'Software Engineer'),
                    'status': att.get('status', 'present'),
                    'check_in_time': att.get('check_in_time'),
                    'check_out_time': att.get('check_out_time'),
                    'is_wfh': att.get('is_wfh', False)
                })
        
        return jsonify({'team_attendance': result, 'count': len(result)}), 200
        
    except Exception as e:
        logger.error(f"Get team attendance error: {str(e)}")
        return jsonify({'error': 'Failed to fetch team attendance'}), 500


@app.route('/api/admin/leave-approvals', methods=['GET'])
@token_required
def get_leave_approvals():
    """Get pending leave approvals for HR or Manager"""
    try:
        current_emp_id = g.current_employee_id
        current_emp = SupabaseDB.select_one('employees', {'employee_id': current_emp_id})
        
        leave_apps = []
        if current_emp and current_emp.get('role') in ['hr', 'admin']:
            # HR sees all pending
            leave_apps = SupabaseDB.select('leave_applications', '*', {'status': 'pending'})
        else:
            # Manager sees only their reports
            reports = SupabaseDB.select('employees', 'employee_id', {'manager_id': current_emp_id})
            report_ids = [r['employee_id'] for r in reports]
            if report_ids:
                all_pending = SupabaseDB.select('leave_applications', '*', {'status': 'pending'})
                leave_apps = [app for app in all_pending if app['employee_id'] in report_ids]

        if leave_apps:
            all_emps = {e['employee_id']: e for e in SupabaseDB.select('employees', '*')}
            for app in leave_apps:
                applicant = all_emps.get(app['employee_id'])
                if applicant:
                    app['employee_name'] = applicant.get('full_name')
                    app['department'] = applicant.get('department')
                    app['designation'] = applicant.get('designation')

        return jsonify({'leave_applications': leave_apps, 'count': len(leave_apps)}), 200
        
    except Exception as e:
        logger.error(f"Get leave approvals error: {str(e)}")
        return jsonify({'error': 'Failed to fetch approvals'}), 500


@app.route('/api/admin/approve-leave/<int:app_id>', methods=['POST'])
@token_required
def approve_leave(app_id):
    """Approve leave application"""
    try:
        data = request.get_json()
        approver_id = g.current_employee_id
        
        leave_app = SupabaseDB.select_one('leave_applications', {'id': app_id})
        if not leave_app:
            return jsonify({'error': 'Application not found'}), 404
            
        current_emp = SupabaseDB.select_one('employees', {'employee_id': approver_id})
        applicant = SupabaseDB.select_one('employees', {'employee_id': leave_app['employee_id']})
        
        is_hr = current_emp and current_emp.get('role') in ['hr', 'admin']
        is_manager = applicant and applicant.get('manager_id') == approver_id
        
        if not (is_hr or is_manager):
            return jsonify({'error': 'Unauthorized to approve this leave'}), 403
        
        # Update status
        SupabaseDB.update('leave_applications', {'id': app_id},
                         {
                             'status': 'approved',
                             'approved_by': approver_id,
                             'approval_date': datetime.now(timezone.utc).isoformat(),
                             'approval_comments': data.get('comments', '')
                         })
        
        # Deduct leave from balance
        LeaveUtils.deduct_leave(leave_app['employee_id'],
                               leave_app['leave_type'],
                               leave_app['number_of_days'])
        
        # Create notification
        NotificationUtils.create_notification(
            leave_app['employee_id'],
            'Leave Approved',
            f'Your {leave_app["leave_type"]} leave has been approved',
            'leave_approved',
            action_url='leave'
        )
        
        log_audit(approver_id, 'APPROVE_LEAVE', 'leave_applications', app_id)
        
        return jsonify({'message': 'Leave approved'}), 200
        
    except Exception as e:
        logger.error(f"Approve leave error: {str(e)}")
        return jsonify({'error': 'Failed to approve leave'}), 500


@app.route('/api/admin/reject-leave/<int:app_id>', methods=['POST'])
@token_required
def reject_leave(app_id):
    """Reject leave application"""
    try:
        data = request.get_json()
        approver_id = g.current_employee_id
        
        leave_app = SupabaseDB.select_one('leave_applications', {'id': app_id})
        if not leave_app:
            return jsonify({'error': 'Application not found'}), 404
            
        current_emp = SupabaseDB.select_one('employees', {'employee_id': approver_id})
        applicant = SupabaseDB.select_one('employees', {'employee_id': leave_app['employee_id']})
        
        is_hr = current_emp and current_emp.get('role') in ['hr', 'admin']
        is_manager = applicant and applicant.get('manager_id') == approver_id
        
        if not (is_hr or is_manager):
            return jsonify({'error': 'Unauthorized to reject this leave'}), 403
        
        # Update status
        SupabaseDB.update('leave_applications', {'id': app_id},
                         {
                             'status': 'rejected',
                             'approved_by': approver_id,
                             'approval_date': datetime.now(timezone.utc).isoformat(),
                             'approval_comments': data.get('comments', '')
                         })
        
        # Create notification
        NotificationUtils.create_notification(
            leave_app['employee_id'],
            'Leave Rejected',
            f'Your {leave_app["leave_type"]} leave has been rejected',
            'leave_rejected',
            action_url='leave'
        )
        
        log_audit(approver_id, 'REJECT_LEAVE', 'leave_applications', app_id)
        
        return jsonify({'message': 'Leave rejected'}), 200
        
    except Exception as e:
        logger.error(f"Reject leave error: {str(e)}")
        return jsonify({'error': 'Failed to reject leave'}), 500


@app.route('/api/notifications', methods=['GET'])
@token_required
def get_notifications():
    """Get recent notifications for the user"""
    try:
        employee_id = g.current_employee_id
        notifications = SupabaseDB.select('notifications', '*', {'employee_id': employee_id})
        
        # Sort by created_at desc
        notifications.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Return top 20
        return jsonify({'notifications': notifications[:20]}), 200
    except Exception as e:
        logger.error(f"Get notifications error: {str(e)}")
        return jsonify({'error': 'Failed to fetch notifications'}), 500

@app.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
@token_required
def mark_notification_read(notif_id):
    """Mark a notification as read"""
    try:
        employee_id = g.current_employee_id
        SupabaseDB.update('notifications', 
                         {'id': notif_id, 'employee_id': employee_id}, 
                         {'is_read': True})
        return jsonify({'message': 'Notification marked as read'}), 200
    except Exception as e:
        logger.error(f"Mark notification read error: {str(e)}")
        return jsonify({'error': 'Failed to mark notification as read'}), 500

@app.route('/api/profile/update-requests', methods=['POST'])
@token_required
def request_profile_update():
    """Employee submits a profile update request"""
    try:
        data = request.get_json()
        employee_id = g.current_employee_id
        
        # Check if the employee is ravi.mallela@otsi.co.in (EMP1105) to bypass approval
        is_bypass = (employee_id == 'EMP1105' or g.current_user.get('email') == 'ravi.mallela@otsi.co.in')
        
        if is_bypass:
            # Directly update the employees table
            allowed_fields = ['full_name', 'phone', 'designation', 'department']
            update_data = {k: v for k, v in data.items() if k in allowed_fields}
            if update_data:
                update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
                SupabaseDB.update('employees', {'employee_id': employee_id}, update_data)
            
            # Log approved request in the request table for auditing
            update_req = {
                'employee_id': employee_id,
                'requested_changes': data,
                'status': 'approved',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'reviewed_by': 'system',
                'review_date': datetime.now(timezone.utc).isoformat()
            }
            SupabaseDB.insert('profile_update_requests', update_req)
            
            log_audit(employee_id, 'UPDATE_PROFILE_BYPASS', 'employees',
                      new_values=update_data)
            return jsonify({'message': 'Profile updated successfully (Bypassed approval).', 'direct': True}), 201
            
        # Insert request into database
        update_req = {
            'employee_id': employee_id,
            'requested_changes': data,
            'status': 'pending',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        req_result = SupabaseDB.insert('profile_update_requests', update_req)
        
        # Notify HR
        hr_users = SupabaseDB.select('employees', 'employee_id', {'role': 'hr'})
        admin_users = SupabaseDB.select('employees', 'employee_id', {'role': 'admin'})
        hr_ids = [u['employee_id'] for u in hr_users + admin_users]
        for nid in set(hr_ids):
            NotificationUtils.create_notification(
                nid,
                'Profile Update Request',
                f'{employee_id} has requested a profile update.',
                'profile_update',
                action_url='profile'
            )
            
        return jsonify({'message': 'Profile update request submitted successfully.', 'direct': False}), 201
    except Exception as e:
        logger.error(f"Request profile update error: {str(e)}")
        return jsonify({'error': 'Failed to submit request'}), 500


@app.route('/api/hr/update-requests', methods=['GET'])
@token_required
@role_required('hr', 'admin')
def get_update_requests():
    """HR gets all pending profile update requests"""
    try:
        reqs = SupabaseDB.select('profile_update_requests', '*', {'status': 'pending'})
        return jsonify({'update_requests': reqs, 'count': len(reqs)}), 200
    except Exception as e:
        logger.error(f"Get update requests error: {str(e)}")
        return jsonify({'error': 'Failed to fetch update requests'}), 500


@app.route('/api/hr/approve-update/<int:req_id>', methods=['POST'])
@token_required
@role_required('hr', 'admin')
def approve_update_request(req_id):
    """HR approves a profile update request"""
    try:
        data = request.get_json()
        approver_id = g.current_employee_id
        action = data.get('action', 'approve') # 'approve' or 'reject'
        
        req_entry = SupabaseDB.select_one('profile_update_requests', {'id': req_id})
        if not req_entry:
            return jsonify({'error': 'Request not found'}), 404
            
        employee_id = req_entry['employee_id']
        requested_changes = req_entry['requested_changes']
        
        if action == 'approve':
            # Map frontend fields to DB fields if needed, or apply directly
            update_data = {
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            if 'phone' in requested_changes: update_data['phone'] = requested_changes['phone']
            if 'email' in requested_changes: update_data['email'] = requested_changes['email']
            if 'department' in requested_changes: update_data['department'] = requested_changes['department']
            if 'team' in requested_changes: update_data['team'] = requested_changes['team']
            if 'designation' in requested_changes: update_data['designation'] = requested_changes['designation']
            if 'full_name' in requested_changes: update_data['full_name'] = requested_changes['full_name']
            if 'manager_id' in requested_changes: 
                update_data['manager_id'] = requested_changes['manager_id']
                mgr = SupabaseDB.select_one('employees', {'employee_id': requested_changes['manager_id']})
                if mgr: update_data['manager_name'] = mgr['full_name']
                
            if update_data:
                SupabaseDB.update('employees', {'employee_id': employee_id}, update_data)
                
            NotificationUtils.create_notification(
                employee_id,
                'Profile Update',
                'Your profile update request was approved.',
                'profile_approved',
                action_url='profile'
            )
            status = 'approved'
        else:
            NotificationUtils.create_notification(
                employee_id,
                'Profile Update',
                'Your profile update request was rejected.',
                'profile_rejected',
                action_url='profile'
            )
            status = 'rejected'
            
        SupabaseDB.update('profile_update_requests', {'id': req_id}, {
            'status': status,
            'reviewed_by': approver_id,
            'review_date': datetime.now(timezone.utc).isoformat()
        })
        
        return jsonify({'message': f'Request {status} successfully.'}), 200
    except Exception as e:
        logger.error(f"Approve update error: {str(e)}")
        return jsonify({'error': 'Failed to process update request'}), 500


@app.route('/api/admin/dashboard-stats', methods=['GET'])
@token_required
def get_dashboard_stats():
    """Get HR/Admin dashboard statistics or Manager reportee statistics."""
    try:
        current_emp_id = g.current_employee_id
        _, is_hr, is_manager, reports, report_ids = get_scope_context(current_emp_id)

        if not (is_hr or is_manager):
            return jsonify({'error': 'Unauthorized'}), 403

        today = date.today().isoformat()
        employees = SupabaseDB.select('employees', '*') if is_hr else reports
        total_employees = len(employees)
        active_employees = len([e for e in employees if classify_employee_record(e) == 'active'])
        inactive_employees = len([e for e in employees if classify_employee_record(e) == 'inactive'])
        pending_registrations = len([e for e in employees if classify_employee_record(e) == 'pending'])

        if is_hr:
            today_attendance = SupabaseDB.select('attendance_logs', '*', {'attendance_date': today})
            all_pending_leaves = SupabaseDB.select('leave_applications', '*', {'status': 'pending'})
            all_pending_corrections = SupabaseDB.select('attendance_correction_requests', '*', {'status': 'pending'})
            open_tickets = SupabaseDB.count('support_tickets', {'status': 'open'})
        else:
            today_attendance = SupabaseDB.select('attendance_logs', '*', {'attendance_date': today, 'employee_id': ('in_', report_ids)}) if report_ids else []
            all_pending_leaves = SupabaseDB.select('leave_applications', '*', {'status': 'pending', 'employee_id': ('in_', report_ids)}) if report_ids else []
            all_pending_corrections = SupabaseDB.select('attendance_correction_requests', '*', {'status': 'pending', 'employee_id': ('in_', report_ids)}) if report_ids else []
            open_tickets = 0

        present_count = len([a for a in today_attendance if a.get('status') in ['present', 'late']])
        live_present_count = len([a for a in today_attendance if a.get('check_in_time') and not a.get('check_out_time')])
        wfh_count = len([a for a in today_attendance if a.get('status') == 'wfh' or a.get('is_wfh')])
        half_day_count = len([a for a in today_attendance if a.get('status') == 'half_day'])
        leave_count = max(0, active_employees - present_count - wfh_count - half_day_count)

        return jsonify({
            'total_employees': total_employees,
            'active_employees': active_employees,
            'inactive_employees': inactive_employees,
            'pending_registrations': pending_registrations,
            'present_today': present_count,
            'live_present_today': live_present_count,
            'wfh_today': wfh_count,
            'half_day_today': half_day_count,
            'leave_today': leave_count,
            'pending_leaves': len(all_pending_leaves),
            'pending_attendance_corrections': len(all_pending_corrections),
            'open_tickets': open_tickets
        }), 200

    except Exception as e:
        logger.error(f"Get dashboard stats error: {str(e)}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500


@app.route('/api/admin/org-overview', methods=['GET'])
@token_required
def get_org_overview():
    """Get grouped organization summaries for admin/HR/manager dashboards."""
    try:
        current_emp_id = g.current_employee_id
        _, is_hr, is_manager, reports, report_ids = get_scope_context(current_emp_id)

        if not (is_hr or is_manager):
            return jsonify({'error': 'Unauthorized'}), 403

        employees = SupabaseDB.select('employees', '*') if is_hr else reports
        project_entries = SupabaseDB.select('timesheet_entries', '*') if is_hr else []

        department_map = defaultdict(list)
        team_map = defaultdict(list)
        manager_map = defaultdict(list)
        for emp in employees:
            department_map[emp.get('department') or 'Unassigned'].append(emp)
            team_map[emp.get('team') or 'Unassigned'].append(emp)
            manager_key = emp.get('manager_name') or emp.get('manager_id') or 'Unassigned'
            manager_map[manager_key].append(emp)

        departments = [
            {'name': key, 'employee_count': len(val)}
            for key, val in sorted(department_map.items(), key=lambda item: item[0].lower())
        ]
        teams = [
            {'name': key, 'employee_count': len(val)}
            for key, val in sorted(team_map.items(), key=lambda item: item[0].lower())
        ]
        managers = [
            {
                'name': key,
                'employee_count': len(val),
                'employee_ids': [emp['employee_id'] for emp in val]
            }
            for key, val in sorted(manager_map.items(), key=lambda item: item[0].lower())
        ]

        project_hours = defaultdict(float)
        for entry in project_entries:
            project_name = entry.get('project_name') or 'Unassigned'
            try:
                project_hours[project_name] += float(entry.get('hours_worked') or 0)
            except Exception:
                continue
        projects = [
            {'name': key, 'total_hours': round(val, 2)}
            for key, val in sorted(project_hours.items(), key=lambda item: item[0].lower())
        ]

        return jsonify({
            'departments': departments,
            'teams': teams,
            'managers': managers,
            'projects': projects,
            'clients': []
        }), 200
    except Exception as e:
        logger.error(f"Org overview error: {str(e)}")
        return jsonify({'error': 'Failed to fetch organization overview'}), 500


@app.route('/api/admin/attendance-report', methods=['GET'])
@token_required
def get_admin_attendance_report():
    """Get daily/monthly attendance logs for any accessible employee."""
    try:
        current_emp_id = g.current_employee_id
        _, is_hr, is_manager, _, report_ids = get_scope_context(current_emp_id)

        if not (is_hr or is_manager):
            return jsonify({'error': 'Unauthorized'}), 403

        employee_id = (request.args.get('employee_id') or '').strip().upper()
        if not employee_id:
            return jsonify({'error': 'employee_id is required'}), 400

        if not is_hr and employee_id not in report_ids:
            return jsonify({'error': 'Unauthorized for this employee'}), 403

        filters = {'employee_id': employee_id}
        exact_date = request.args.get('date')
        month = request.args.get('month')
        year = request.args.get('year')

        attendance_logs = SupabaseDB.select('attendance_logs', '*', filters)
        if exact_date:
            attendance_logs = [log for log in attendance_logs if log.get('attendance_date') == exact_date]
        elif month and year:
            prefix = f"{int(year):04d}-{int(month):02d}-"
            attendance_logs = [log for log in attendance_logs if (log.get('attendance_date') or '').startswith(prefix)]

        attendance_logs.sort(key=lambda x: x.get('attendance_date', ''), reverse=True)
        employee = SupabaseDB.select_one('employees', {'employee_id': employee_id})

        return jsonify({
            'employee': {
                'employee_id': employee_id,
                'full_name': employee.get('full_name') if employee else employee_id,
                'designation': employee.get('designation') if employee else None,
                'department': employee.get('department') if employee else None,
                'manager_name': employee.get('manager_name') if employee else None
            },
            'attendance_logs': attendance_logs,
            'count': len(attendance_logs)
        }), 200
    except Exception as e:
        logger.error(f"Admin attendance report error: {str(e)}")
        return jsonify({'error': 'Failed to fetch attendance report'}), 500


@app.route('/api/admin/export-attendance', methods=['GET'])
@token_required
@role_required('hr', 'admin')
def export_attendance_csv():
    """Export attendance data to CSV"""
    try:
        # Get all attendance records
        records = SupabaseDB.select('attendance_logs', '*')
        
        # Sort by date descending
        records.sort(key=lambda x: x.get('attendance_date', ''), reverse=True)
        
        # Create CSV in memory
        si = io.StringIO()
        cw = csv.writer(si)
        
        # Write header
        cw.writerow(['Attendance ID', 'Employee ID', 'Date', 'Check In', 'Check Out', 'Status', 'Working Hours', 'Location', 'Notes'])
        
        # Write rows
        for r in records:
            cw.writerow([
                r.get('id', ''),
                r.get('employee_id', ''),
                r.get('attendance_date', ''),
                r.get('check_in_time', ''),
                r.get('check_out_time', ''),
                r.get('status', ''),
                r.get('working_hours', ''),
                r.get('location', ''),
                r.get('notes', '')
            ])
            
        output = si.getvalue()
        
        from flask import Response
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=attendance_export.csv"}
        )
        
    except Exception as e:
        logger.error(f"Export attendance error: {str(e)}")
        return jsonify({'error': 'Failed to export data'}), 500


@app.route('/api/admin/tickets', methods=['GET'])
@token_required
def get_all_tickets():
    """Get all support tickets (Admin/SNA only)"""
    try:
        # Check if admin or SNA team
        employee_id = g.current_employee_id
        emp = SupabaseDB.select_one('employees', {'employee_id': employee_id})
        if not emp or (emp['role'] != 'admin' and emp.get('team') != 'SNA'):
            return jsonify({'error': 'Unauthorized'}), 403
            
        tickets = SupabaseDB.select('support_tickets', '*')
        # Sort by creation date descending
        tickets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return jsonify({'tickets': tickets}), 200
    except Exception as e:
        logger.error(f"Get all tickets error: {str(e)}")
        return jsonify({'error': 'Failed to fetch tickets'}), 500

@app.route('/api/admin/tickets/<int:ticket_id>/update', methods=['POST'])
@token_required
def update_ticket(ticket_id):
    """Update support ticket status and response (Admin/SNA only)"""
    try:
        data = request.get_json()
        employee_id = g.current_employee_id
        emp = SupabaseDB.select_one('employees', {'employee_id': employee_id})
        if not emp or (emp['role'] not in ['admin', 'hr'] and emp.get('team') != 'SNA'):
            return jsonify({'error': 'Unauthorized'}), 403
            
        status = data.get('status')
        response_text = data.get('response') or data.get('resolution')
        
        ticket = SupabaseDB.select_one('support_tickets', {'id': ticket_id})
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
            
        update_data = {'updated_at': datetime.now(timezone.utc).isoformat()}
        if status:
            update_data['status'] = status
            if status in ['resolved', 'closed']:
                update_data['resolved_date'] = datetime.now(timezone.utc).isoformat()
        if response_text: 
            update_data['resolution'] = response_text
            
        SupabaseDB.update('support_tickets', {'id': ticket_id}, update_data)
        
        # Notify the ticket creator
        try:
            if status or response_text:
                msg = f"Your ticket '{ticket['subject']}' was updated."
                if status: msg += f" Status changed to {status}."
                NotificationUtils.create_notification(
                    ticket['employee_id'],
                    'Ticket Update',
                    msg,
                    'ticket_update',
                    action_url='hd'
                )
        except Exception as notif_err:
            logger.error(f"Ticket update notification warning: {notif_err}")
            
        return jsonify({'message': 'Ticket updated successfully'}), 200
    except Exception as e:
        logger.error(f"Update ticket error: {str(e)}")
        return jsonify({'error': 'Failed to update ticket'}), 500


# ═════════════════════════════════════════════════════════════
# LEAVE & ATTENDANCE CORRECTION ENHANCEMENTS
# ═════════════════════════════════════════════════════════════

@app.route('/api/leave/cancel/<int:app_id>', methods=['POST'])
@token_required
def cancel_leave(app_id):
    """Cancel a pending leave application"""
    try:
        employee_id = g.current_employee_id
        
        app_record = SupabaseDB.select_one('leave_applications', {'id': app_id})
        if not app_record:
            return jsonify({'error': 'Leave application not found'}), 404
            
        if app_record['employee_id'] != employee_id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        if app_record['status'] != 'pending':
            return jsonify({'error': f"Cannot cancel leave with status '{app_record['status']}'"}), 400
            
        # Update status
        SupabaseDB.update('leave_applications', {'id': app_id}, {'status': 'cancelled'})
        
        # Notify HR
        hr_emps = SupabaseDB.select('employees', 'employee_id', {'role': 'hr'})
        for hr in hr_emps:
            NotificationUtils.create_notification(
                hr['employee_id'],
                'Leave Cancelled',
                f'{employee_id} has cancelled their pending {app_record["leave_type"]} leave application.',
                'leave_cancelled',
                action_url='profile'
            )
            
        log_audit(employee_id, 'CANCEL_LEAVE', 'leave_applications', entity_id=app_id)
        return jsonify({'message': 'Leave application cancelled successfully'}), 200
        
    except Exception as e:
        logger.error(f"Cancel leave error: {str(e)}")
        return jsonify({'error': 'Failed to cancel leave'}), 500


@app.route('/api/attendance/correction/request', methods=['POST'])
@token_required
def request_attendance_correction():
    """Submit a request for attendance correction"""
    try:
        employee_id = g.current_employee_id
        data = request.get_json()
        
        required = ['attendance_date', 'reason']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
            
        attendance_date = data['attendance_date']
        actual_check_in = data.get('actual_check_in') or data.get('requested_check_in')
        actual_check_out = data.get('actual_check_out') or data.get('requested_check_out')
        
        if not actual_check_in and not actual_check_out:
            return jsonify({'error': 'Must provide either check-in or check-out time'}), 400

        def convert_naive_to_utc(dt_str):
            if not dt_str: return None
            if dt_str.endswith('Z'): return dt_str
            # Assume naive string from frontend is IST (+05:30)
            from dateutil.parser import parse
            dt = parse(dt_str)
            if dt.tzinfo is None:
                ist_tz = timezone(timedelta(hours=5, minutes=30))
                dt = dt.replace(tzinfo=ist_tz)
            return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

        final_check_in = convert_naive_to_utc(actual_check_in)
        final_check_out = convert_naive_to_utc(actual_check_out)

        # Validate against future times using UTC
        now_utc = datetime.now(timezone.utc)
        if final_check_in:
            try:
                in_dt = datetime.fromisoformat(final_check_in.replace('Z', '+00:00'))
                if in_dt.tzinfo is None:
                    in_dt = in_dt.replace(tzinfo=timezone.utc)
                if in_dt > now_utc:
                    return jsonify({'error': 'Check-in time cannot be in the future'}), 400
            except Exception:
                pass
                
        if final_check_out:
            try:
                out_dt = datetime.fromisoformat(final_check_out.replace('Z', '+00:00'))
                if out_dt.tzinfo is None:
                    out_dt = out_dt.replace(tzinfo=timezone.utc)
                if out_dt > now_utc:
                    return jsonify({'error': 'Check-out time cannot be in the future'}), 400
                
                # Check-out must be after check-in
                effective_check_in_str = final_check_in
                if not effective_check_in_str:
                    # Look up existing attendance log for this date
                    att_log_check = SupabaseDB.select_one('attendance_logs', {
                        'employee_id': employee_id,
                        'attendance_date': attendance_date
                    })
                    if att_log_check:
                        effective_check_in_str = att_log_check.get('check_in_time')
                
                if effective_check_in_str:
                    in_dt_check = datetime.fromisoformat(effective_check_in_str.replace('Z', '+00:00'))
                    if in_dt_check.tzinfo is None:
                        in_dt_check = in_dt_check.replace(tzinfo=timezone.utc)
                    if out_dt <= in_dt_check:
                        return jsonify({'error': 'Check-out time must be after check-in time. Did you enter AM instead of PM?'}), 400
            except Exception:
                pass
                
        reason = data['reason']
        
        correction_data = {
            'employee_id': employee_id,
            'attendance_date': attendance_date,
            'actual_check_in': final_check_in,
            'actual_check_out': final_check_out,
            'reason': reason,
            'status': 'pending',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        existing = SupabaseDB.select_one('attendance_correction_requests', {
            'employee_id': employee_id,
            'attendance_date': attendance_date
        })
        
        if existing:
            if existing['status'] == 'pending':
                return jsonify({'error': 'A pending correction request already exists for this date'}), 400
            
            # Re-submit request
            req = SupabaseDB.update('attendance_correction_requests', {'id': existing['id']}, {
                'actual_check_in': final_check_in,
                'actual_check_out': final_check_out,
                'reason': reason,
                'status': 'pending',
                'updated_at': datetime.now(timezone.utc).isoformat()
            })
        else:
            req = SupabaseDB.insert('attendance_correction_requests', correction_data)
            
        # Fallback to query request from database if req/insert/update returned None
        if not req:
            req = SupabaseDB.select_one('attendance_correction_requests', {
                'employee_id': employee_id,
                'attendance_date': attendance_date
            })

        req_id = req['id'] if req else (existing['id'] if existing else None)

        # Fire-and-forget: notify HR/Admins/Manager in the background so the
        # response is returned immediately without waiting for multiple DB calls.
        def _notify_and_audit(emp_id, att_date, rsn, r_id):
            try:
                employee_details = SupabaseDB.select_one('employees', {'employee_id': emp_id})
                manager_id = employee_details.get('manager_id') if employee_details else None
                employee_name = (employee_details.get('full_name') if employee_details else None) or emp_id

                hr_users = SupabaseDB.select('employees', 'employee_id', {'role': 'hr'})
                admin_users = SupabaseDB.select('employees', 'employee_id', {'role': 'admin'})
                notify_ids = set()
                for emp in hr_users:
                    notify_ids.add(emp['employee_id'])
                for emp in admin_users:
                    notify_ids.add(emp['employee_id'])
                if manager_id:
                    notify_ids.add(manager_id)

                notif_title = 'Attendance Correction Request'
                notif_msg = (f'{employee_name} has requested attendance correction '
                             f'for {att_date}. Reason: {rsn}')
                notif_url = f'attendance_correction:{r_id}' if r_id else 'attendance_correction'

                for nid in notify_ids:
                    NotificationUtils.create_notification(
                        nid, notif_title, notif_msg,
                        'attendance_correction', action_url=notif_url
                    )

                log_audit(emp_id, 'REQUEST_ATTENDANCE_CORRECTION',
                          'attendance_correction_requests', entity_id=r_id)
            except Exception as bg_err:
                logger.error(f"Background notification error for correction: {bg_err}")

        threading.Thread(
            target=_notify_and_audit,
            args=(employee_id, attendance_date, reason, req_id),
            daemon=True
        ).start()

        return jsonify({'message': 'Correction request submitted successfully'}), 201
        
    except Exception as e:
        err_str = str(e)
        logger.error(f"Request attendance correction error: {err_str}")
        if '42501' in err_str or 'row-level security' in err_str.lower():
            return jsonify({'error': 'Database permission denied: Please disable Row Level Security (RLS) on attendance_correction_requests table in Supabase.'}), 500
        return jsonify({'error': f'Failed to submit correction request: {err_str}'}), 500


@app.route('/api/attendance/correction/history', methods=['GET'])
@token_required
def get_attendance_correction_history():
    """Get past and pending attendance correction requests for current employee"""
    try:
        employee_id = g.current_employee_id
        
        reqs = SupabaseDB.select('attendance_correction_requests', '*', {'employee_id': employee_id})
        
        # Sort by created_at desc
        reqs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                
        return jsonify({'corrections': reqs}), 200
    except Exception as e:
        logger.error(f"Get attendance correction history error: {str(e)}")
        return jsonify({'error': 'Failed to fetch correction history'}), 500


@app.route('/api/hr/attendance-corrections', methods=['GET'])
@token_required
def get_attendance_corrections():
    """Get pending attendance correction requests (HR gets all, Managers get reportees)"""
    try:
        current_emp_id = g.current_employee_id
        current_emp = SupabaseDB.select_one('employees', {'employee_id': current_emp_id})
        
        is_hr = current_emp and current_emp.get('role') in ['hr', 'admin']
        
        # Check if they have reportees
        reports = SupabaseDB.select('employees', 'employee_id', {'manager_id': current_emp_id})
        report_ids = [r['employee_id'] for r in reports]
        is_manager = len(report_ids) > 0
        
        if not (is_hr or is_manager):
            return jsonify({'error': 'Unauthorized'}), 403
            
        reqs = SupabaseDB.select('attendance_correction_requests', '*', {'status': 'pending'})
        
        if not is_hr:
            reqs = [r for r in reqs if r['employee_id'] in report_ids]
        
        if reqs:
            all_emps = {e['employee_id']: e for e in SupabaseDB.select('employees', '*')}
            for r in reqs:
                emp = all_emps.get(r['employee_id'])
                if emp:
                    r['employee_name'] = emp['full_name']
                    r['department'] = emp.get('department')
                
        return jsonify({'corrections': reqs, 'count': len(reqs)}), 200
    except Exception as e:
        logger.error(f"Get attendance corrections error: {str(e)}")
        return jsonify({'error': 'Failed to fetch correction requests'}), 500


@app.route('/api/hr/approve-correction/<int:req_id>', methods=['POST'])
@token_required
def approve_attendance_correction(req_id):
    """Approve a pending correction request and update attendance log"""
    try:
        hr_id = g.current_employee_id
        req_record = SupabaseDB.select_one('attendance_correction_requests', {'id': req_id})
        if not req_record:
            return jsonify({'error': 'Correction request not found'}), 404
            
        if req_record['status'] != 'pending':
            return jsonify({'error': 'Request is not pending'}), 400
            
        current_emp = SupabaseDB.select_one('employees', {'employee_id': hr_id})
        applicant = SupabaseDB.select_one('employees', {'employee_id': req_record['employee_id']})
        
        is_hr = current_emp and current_emp.get('role') in ['hr', 'admin']
        is_manager = applicant and applicant.get('manager_id') == hr_id
        
        if not (is_hr or is_manager):
            return jsonify({'error': 'Unauthorized to approve this correction'}), 403
            
        emp_id = req_record['employee_id']
        att_date = req_record['attendance_date']
        
        working_hours = None
        
        att_log = SupabaseDB.select_one('attendance_logs', {
            'employee_id': emp_id,
            'attendance_date': att_date
        })
        
        final_check_in = req_record.get('actual_check_in')
        if not final_check_in and att_log:
            final_check_in = att_log.get('check_in_time')
            
        final_check_out = req_record.get('actual_check_out')
        if not final_check_out and att_log:
            final_check_out = att_log.get('check_out_time')
            
        if final_check_in and final_check_out:
            try:
                in_str = final_check_in if (final_check_in.endswith('Z') or '+' in final_check_in[10:]) else final_check_in + 'Z'
                out_str = final_check_out if (final_check_out.endswith('Z') or '+' in final_check_out[10:]) else final_check_out + 'Z'
                in_time = datetime.fromisoformat(in_str.replace('Z', '+00:00'))
                out_time = datetime.fromisoformat(out_str.replace('Z', '+00:00'))
                working_hours = round((out_time - in_time).total_seconds() / 3600.0, 2)
            except Exception as ex:
                logger.error(f"Error parsing correction times: {ex}")
                
        is_wfh = False
        if att_log:
            is_wfh = att_log.get('is_wfh', False)
            
        status = 'wfh' if is_wfh else 'present'
        
        try:
            if final_check_in:
                in_utc = datetime.fromisoformat(final_check_in.replace('Z', ''))
                # Convert the stored UTC string to IST (+05:30) before checking hours/minutes
                in_ist = in_utc + timedelta(hours=5, minutes=30)
                in_hour = in_ist.hour
                in_min = in_ist.minute
                is_late = (in_hour == 9 and in_min > 15) or in_hour > 9
                if is_late and not is_wfh:
                    status = 'late'
            else:
                is_late = False
        except Exception:
            is_late = False
            
        att_data = {
            'employee_id': emp_id,
            'attendance_date': att_date,
            'check_in_time': final_check_in,
            'check_out_time': final_check_out,
            'working_hours': working_hours,
            'status': status,
            'is_late': is_late,
            'location_verified': True,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        if att_log:
            SupabaseDB.update('attendance_logs', {'id': att_log['id']}, att_data)
        else:
            att_data['check_in_location'] = 'OTSi Office'
            SupabaseDB.insert('attendance_logs', att_data)
            
        SupabaseDB.update('attendance_correction_requests', {'id': req_id}, {
            'status': 'approved',
            'reviewed_by': hr_id,
            'review_date': datetime.now(timezone.utc).isoformat()
        })
        
        # Send notification and audit log — isolated so they never break the approval response
        try:
            NotificationUtils.create_notification(
                emp_id,
                'Attendance Correction Approved',
                f'Your attendance correction request for {att_date} has been approved.',
                'attendance_correction_approved',
                action_url='att'
            )
        except Exception as notif_err:
            logger.error(f"Notification error after approval: {notif_err}")

        try:
            log_audit(hr_id, 'APPROVE_ATTENDANCE_CORRECTION', 'attendance_correction_requests', 
                      entity_id=req_id)
        except Exception as audit_err:
            logger.error(f"Audit log error after approval: {audit_err}")
                  
        return jsonify({'message': 'Correction request approved successfully'}), 200
        
    except Exception as e:
        logger.error(f"Approve correction error: {str(e)}")
        return jsonify({'error': 'Failed to approve request'}), 500


@app.route('/api/hr/reject-correction/<int:req_id>', methods=['POST'])
@token_required
def reject_attendance_correction(req_id):
    """Reject a pending correction request"""
    try:
        hr_id = g.current_employee_id
        data = request.get_json() or {}
        comments = data.get('comments', '')
        
        req_record = SupabaseDB.select_one('attendance_correction_requests', {'id': req_id})
        if not req_record:
            return jsonify({'error': 'Correction request not found'}), 404
            
        if req_record['status'] != 'pending':
            return jsonify({'error': 'Request is not pending'}), 400
            
        current_emp = SupabaseDB.select_one('employees', {'employee_id': hr_id})
        applicant = SupabaseDB.select_one('employees', {'employee_id': req_record['employee_id']})
        
        is_hr = current_emp and current_emp.get('role') in ['hr', 'admin']
        is_manager = applicant and applicant.get('manager_id') == hr_id
        
        if not (is_hr or is_manager):
            return jsonify({'error': 'Unauthorized to reject this correction'}), 403
            
        SupabaseDB.update('attendance_correction_requests', {'id': req_id}, {
            'status': 'rejected',
            'reviewed_by': hr_id,
            'review_date': datetime.now(timezone.utc).isoformat(),
            'comments': comments
        })
        
        NotificationUtils.create_notification(
            req_record['employee_id'],
            'Attendance Correction Rejected',
            f'Your attendance correction request for {req_record["attendance_date"]} has been rejected. Reason: {comments}',
            'attendance_correction_rejected',
            action_url='att'
        )
        
        log_audit(hr_id, 'REJECT_ATTENDANCE_CORRECTION', 'attendance_correction_requests', 
                  entity_id=req_id, new_values={'comments': comments})
                  
        return jsonify({'message': 'Correction request rejected successfully'}), 200
        
    except Exception as e:
        logger.error(f"Reject correction error: {str(e)}")
        return jsonify({'error': 'Failed to reject request'}), 500


# ═════════════════════════════════════════════════════════════
# HOLIDAYS ENDPOINTS
# ═════════════════════════════════════════════════════════════

OFFICIAL_FALLBACK_HOLIDAYS_2026 = [
    # 1. OTSI INDIA OFFICIAL HOLIDAYS 2026 (14 Days)
    {"id": 1, "holiday_date": "2026-01-01", "occasion": "New Year Day", "remark": "All Locations", "region": "India"},
    {"id": 2, "holiday_date": "2026-01-14", "occasion": "Sankranti / Pongal", "remark": "All Locations excluding Bangalore", "region": "India"},
    {"id": 3, "holiday_date": "2026-01-15", "occasion": "Makara Sankranti", "remark": "Only Bangalore", "region": "India"},
    {"id": 4, "holiday_date": "2026-01-26", "occasion": "Republic Day", "remark": "All Locations", "region": "India"},
    {"id": 5, "holiday_date": "2026-03-03", "occasion": "Holi", "remark": "Only Delhi", "region": "India"},
    {"id": 6, "holiday_date": "2026-03-19", "occasion": "Ugadi", "remark": "All Locations excluding Delhi", "region": "India"},
    {"id": 7, "holiday_date": "2026-05-01", "occasion": "Budha Purnima / May Day", "remark": "All Locations excluding Bangalore", "region": "India"},
    {"id": 8, "holiday_date": "2026-05-27", "occasion": "Eidul Azha (Bakrid)", "remark": "All Locations", "region": "India"},
    {"id": 9, "holiday_date": "2026-09-14", "occasion": "Vinayaka Chavithi", "remark": "All Locations", "region": "India"},
    {"id": 10, "holiday_date": "2026-10-02", "occasion": "Mahatma Gandhi Jayanthi", "remark": "All Locations", "region": "India"},
    {"id": 11, "holiday_date": "2026-10-20", "occasion": "Vijaya Dasami (Dussehra)", "remark": "All Locations excluding Bangalore", "region": "India"},
    {"id": 12, "holiday_date": "2026-10-21", "occasion": "Following Day of Vijaya Dasami", "remark": "Only Bangalore", "region": "India"},
    {"id": 13, "holiday_date": "2026-11-10", "occasion": "Balipadyami", "remark": "Only Bangalore", "region": "India"},
    {"id": 14, "holiday_date": "2026-12-25", "occasion": "Christmas", "remark": "All Locations", "region": "India"},
    # 2. OTSI US OFFICIAL HOLIDAYS 2026 (9 Days)
    {"id": 15, "holiday_date": "2026-01-01", "occasion": "New Year's Day", "remark": "All US Locations", "region": "US"},
    {"id": 16, "holiday_date": "2026-01-19", "occasion": "Martin Luther King Jr. Day", "remark": "All US Locations", "region": "US"},
    {"id": 17, "holiday_date": "2026-05-25", "occasion": "Memorial Day", "remark": "All US Locations", "region": "US"},
    {"id": 18, "holiday_date": "2026-06-19", "occasion": "Juneteenth National Independence Day", "remark": "All US Locations", "region": "US"},
    {"id": 19, "holiday_date": "2026-07-03", "occasion": "Independence Day (Observed)", "remark": "All US Locations", "region": "US"},
    {"id": 20, "holiday_date": "2026-09-07", "occasion": "Labor Day", "remark": "All US Locations", "region": "US"},
    {"id": 21, "holiday_date": "2026-11-26", "occasion": "Thanksgiving Day", "remark": "All US Locations", "region": "US"},
    {"id": 22, "holiday_date": "2026-11-27", "occasion": "Day After Thanksgiving", "remark": "All US Locations", "region": "US"},
    {"id": 23, "holiday_date": "2026-12-25", "occasion": "Christmas Day", "remark": "All US Locations", "region": "US"}
]

@app.route('/api/holidays', methods=['GET'])
@token_required
def get_holidays():
    """Get all company holidays with database lookup and instant 2026 calendar fallback"""
    try:
        holidays = SupabaseDB.select('holidays')
        if holidays and len(holidays) > 0:
            holidays.sort(key=lambda x: x['holiday_date'])
            return jsonify(holidays), 200
    except Exception as e:
        logger.warning(f"Could not load holidays from Supabase table ({e}); serving official 2026 calendar fallback.")
        
    return jsonify(OFFICIAL_FALLBACK_HOLIDAYS_2026), 200

@app.route('/api/holidays', methods=['POST'])
@token_required
@role_required('admin', 'hr')
def add_holiday():
    """Add a new holiday"""
    try:
        data = request.get_json()
        required = ['holiday_date', 'occasion']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
            
        new_holiday = {
            'holiday_date': data['holiday_date'],
            'occasion': data['occasion'],
            'remark': data.get('remark', ''),
            'region': data.get('region', 'India')
        }
        
        result = SupabaseDB.insert('holidays', new_holiday)
        return jsonify({'message': 'Holiday added successfully', 'holiday': result}), 201
    except Exception as e:
        logger.error(f"Add holiday error: {str(e)}")
        return jsonify({'error': 'Failed to add holiday'}), 500

@app.route('/api/holidays/<int:holiday_id>', methods=['DELETE'])
@token_required
@role_required('admin', 'hr')
def delete_holiday(holiday_id):
    """Delete a holiday"""
    try:
        success = SupabaseDB.delete('holidays', {'id': holiday_id})
        if success:
            return jsonify({'message': 'Holiday deleted successfully'}), 200
        else:
            return jsonify({'error': 'Holiday not found'}), 404
    except Exception as e:
        logger.error(f"Delete holiday error: {str(e)}")
        return jsonify({'error': 'Failed to delete holiday'}), 500

@app.route('/api/holidays/<int:holiday_id>', methods=['PUT'])
@token_required
@role_required('admin', 'hr')
def update_holiday(holiday_id):
    """Update an existing holiday"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        update_data = {}
        if 'holiday_date' in data:
            update_data['holiday_date'] = data['holiday_date']
        if 'occasion' in data:
            update_data['occasion'] = data['occasion']
        if 'remark' in data:
            update_data['remark'] = data['remark']
        if 'region' in data:
            update_data['region'] = data['region']
            
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
            
        # SupabaseDB.update method updates records matching the condition
        result = SupabaseDB.update('holidays', {'id': holiday_id}, update_data)
        return jsonify({'message': 'Holiday updated successfully', 'holiday': result}), 200
    except Exception as e:
        logger.error(f"Update holiday error: {str(e)}")
        return jsonify({'error': 'Failed to update holiday'}), 500

# ═════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal error: {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500


# ═════════════════════════════════════════════════════════════
# RUN APPLICATION
# ═════════════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.getenv('SERVER_PORT', 5000))
    host = os.getenv('SERVER_HOST', '0.0.0.0')
    debug = FLASK_ENV == 'development'
    
    logger.info(f"Starting OTSI Attendance Portal API on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
