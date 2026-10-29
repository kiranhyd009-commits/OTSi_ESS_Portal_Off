#!/usr/bin/env python
"""
Create or reset the fixed OTSI admin account.

Creates:
- Employee ID: OTSI0001
- Email: admin.otsi@otsi-usa.com
- Role: admin
- Status: active

Usage:
  python create_super_admin_otsi.py
  python create_super_admin_otsi.py MyTempPassword@123
"""

import os
import sys
import secrets
import logging
from datetime import datetime, date, timezone

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from supabase import create_client, Client

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EMPLOYEE_ID = 'OTSI0001'
EMAIL = 'admin.otsi@otsi-usa.com'
FULL_NAME = 'OTSI Administrator'
DESIGNATION = 'System Administrator'
DEPARTMENT = 'Administration'


def get_supabase_client() -> Client:
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    if not supabase_url or not supabase_key:
        raise ValueError('SUPABASE_URL and SUPABASE_KEY must be set in the environment')
    schema = os.getenv('SUPABASE_SCHEMA', 'public').strip() or 'public'
    from supabase.lib.client_options import ClientOptions
    return create_client(supabase_url, supabase_key, options=ClientOptions(schema=schema))



def ensure_admin_account(client: Client, password: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    password_hash = generate_password_hash(password)

    record = {
        'employee_id': EMPLOYEE_ID,
        'email': EMAIL,
        'full_name': FULL_NAME,
        'designation': DESIGNATION,
        'department': DEPARTMENT,
        'password_hash': password_hash,
        'role': 'admin',
        'status': 'active',
        'date_of_joining': date.today().isoformat(),
        'updated_at': now,
        'password_changed_at': now,
        'failed_login_attempts': 0,
        'lockout_until': None,
        'mfa_enabled': False,
        'mfa_temp_code': None,
        'mfa_temp_expires': None
    }

    existing = client.table('employees').select('*').eq('employee_id', EMPLOYEE_ID).execute()
    if not existing.data:
        existing = client.table('employees').select('*').eq('email', EMAIL).execute()

    if existing.data and isinstance(existing.data, list) and len(existing.data) > 0:
        first_record = existing.data[0]
        current_emp_id = first_record.get('employee_id', EMPLOYEE_ID) if isinstance(first_record, dict) else EMPLOYEE_ID
        client.table('employees').update(record).eq('employee_id', current_emp_id).execute()
        logger.info('Updated existing OTSI admin account')
    else:
        record['created_at'] = now
        client.table('employees').insert([record]).execute()
        logger.info('Created new OTSI admin account')

    leave_balance = client.table('leave_balance').select('*').eq('employee_id', EMPLOYEE_ID).execute()
    if not leave_balance.data:
        client.table('leave_balance').insert([{
            'employee_id': EMPLOYEE_ID,
            'casual_leave': 12,
            'sick_leave': 8,
            'earned_leave': 20.0,
            'bereavement_leave': 3,
            'marriage_leave': 0,
            'lop_leave': 0,
            'created_at': now,
            'updated_at': now
        }]).execute()
        logger.info('Created leave balance for OTSI admin account')

    try:
        client.table('password_history').insert([{
            'employee_id': EMPLOYEE_ID,
            'password_hash': password_hash,
            'created_at': now
        }]).execute()
    except Exception as exc:
        logger.warning(f'Could not add password history: {exc}')



def main() -> int:
    try:
        password = sys.argv[1].strip() if len(sys.argv) > 1 and sys.argv[1].strip() else secrets.token_urlsafe(10)
        client = get_supabase_client()
        ensure_admin_account(client, password)

        print('\nOTSI admin account is ready:\n')
        print(f'  Employee ID : {EMPLOYEE_ID}')
        print(f'  Email       : {EMAIL}')
        print(f'  Role        : admin')
        print(f'  Status      : active')
        print(f'  Password    : {password}')
        print('\nUse role "admin" while signing in.\n')
        return 0
    except Exception as exc:
        logger.error(f'Failed to create OTSI admin account: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
