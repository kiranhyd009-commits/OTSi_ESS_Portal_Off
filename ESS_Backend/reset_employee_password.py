import sys
import os
from dotenv import load_dotenv

# Ensure we can load configuration and import database
load_dotenv()
from database import SupabaseDB
from auth import AuthUtils

def main():
    if len(sys.argv) < 2:
        print("Usage: python reset_employee_password.py <EMPLOYEE_ID> [NEW_PASSWORD]")
        print("Example: python reset_employee_password.py EMP1002")
        print("Example: python reset_employee_password.py EMP1002 Password@999")
        sys.exit(1)
        
    emp_id = sys.argv[1].strip().upper()
    password = sys.argv[2] if len(sys.argv) > 2 else 'R@vikiran332!'
    
    # 1. Fetch employee details
    emp = SupabaseDB.select_one('employees', {'employee_id': emp_id})
    if not emp:
        print(f"❌ Error: Employee with ID '{emp_id}' not found in the database.")
        sys.exit(1)
        
    # 2. Hash and update
    new_hash = AuthUtils.hash_password(password)
    SupabaseDB.update('employees', {'employee_id': emp_id}, {
        'password_hash': new_hash,
        'status': 'active',
        'failed_login_attempts': 0,
        'lockout_until': None
    })
    
    print(f"✅ Successfully reset password for employee:")
    print(f"   Name:         {emp.get('full_name')}")
    print(f"   Email:        {emp.get('email')}")
    print(f"   Employee ID:  {emp_id}")
    print(f"   New Password: {password}")
    print(f"   Status:       active (unlocked)")

if __name__ == '__main__':
    main()
