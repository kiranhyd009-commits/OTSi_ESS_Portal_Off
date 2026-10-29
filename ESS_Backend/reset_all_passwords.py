import sys
import os
from dotenv import load_dotenv

# Ensure we can load configuration and import database
load_dotenv()
from database import SupabaseDB
from auth import AuthUtils

def main():
    password = sys.argv[1] if len(sys.argv) > 1 else 'M@llem5831!'
    
    print(f"Preparing to update password for ALL employees to: '{password}'")
    
    # 1. Fetch all employees
    employees = SupabaseDB.select('employees', 'id, employee_id, full_name, email')
    if not employees:
        print("Error: No employees found in the database.")
        sys.exit(1)
        
    print(f"Found {len(employees)} employee(s). Updating passwords...")
    
    # 2. Hash password once
    new_hash = AuthUtils.hash_password(password)
    
    updated_count = 0
    failed_count = 0
    
    for emp in employees:
        emp_id = emp.get('employee_id')
        full_name = emp.get('full_name', 'Unknown')
        
        try:
            SupabaseDB.update('employees', {'employee_id': emp_id}, {
                'password_hash': new_hash,
                'status': 'active',
                'failed_login_attempts': 0,
                'lockout_until': None
            })
            updated_count += 1
            print(f"  [SUCCESS] Updated [{emp_id}] - {full_name}")
        except Exception as e:
            failed_count += 1
            print(f"  [ERROR] Failed [{emp_id}] - {full_name}: {e}")

    print("\n" + "="*50)
    print("Password update completed!")
    print(f"   Total Processed: {len(employees)}")
    print(f"   Successfully Updated: {updated_count}")
    print(f"   Failed: {failed_count}")
    print(f"   New Common Password: {password}")
    print("="*50)

if __name__ == '__main__':
    main()
