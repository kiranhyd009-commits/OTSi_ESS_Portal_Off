#!/usr/bin/env python3
"""
OTSi ESS Portal - Daily Attendance Check-in Generator / Simulator
Inserts realistic check-in records for all active employees for today or any given date.
Works directly with Supabase via REST API and outputs a companion SQL file (checkin_today.sql).

Usage:
    python run_checkin_today.py                     # Check in all active employees for today
    python run_checkin_today.py yesterday           # Run for yesterday
    python run_checkin_today.py 2026-10-27          # Run for specific date
    python run_checkin_today.py --force             # Overwrite/update existing check-ins
"""

import sys
import os
import random
from datetime import datetime, date, timedelta, timezone
from dotenv import load_dotenv

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from database import SupabaseDB

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TARGET_DATE = None

# Official OTSI Company Holidays Calendar (2026)
OFFICIAL_HOLIDAYS_2026 = {
    '2026-01-01': ('New Year Day', 'All Locations'),
    '2026-01-14': ('Sankranti / Pongal', 'All Locations excluding Bangalore'),
    '2026-01-15': ('Makara Sankranti', 'Only Bangalore'),
    '2026-01-26': ('Republic Day', 'All Locations'),
    '2026-03-03': ('Holi', 'Only Delhi'),
    '2026-03-19': ('Ugadi', 'All Locations excluding Delhi'),
    '2026-05-01': ('Budha Purnima / May Day', 'All Locations excluding Bangalore'),
    '2026-05-27': ('Eidul Azha (Bakrid)', 'All Locations'),
    '2026-09-14': ('Vinayaka Chavithi', 'All Locations'),
    '2026-10-02': ('Mahatma Gandhi Jayanthi', 'All Locations'),
    '2026-10-20': ('Vijaya Dasami (Dussehra)', 'All Locations excluding Bangalore'),
    '2026-10-21': ('Following Day of Vijaya Dasami', 'Only Bangalore'),
    '2026-11-10': ('Balipadyami', 'Only Bangalore'),
    '2026-12-25': ('Christmas', 'All Locations')
}

def get_company_holiday(target_date_str):
    """Check if a date is an official OTSI company holiday (from list or database)."""
    if target_date_str in OFFICIAL_HOLIDAYS_2026:
        return OFFICIAL_HOLIDAYS_2026[target_date_str]
    try:
        db_hols = SupabaseDB.select('holidays', '*', {'holiday_date': target_date_str})
        if db_hols:
            h = db_hols[0]
            return (h.get('occasion', 'Company Holiday'), h.get('remark', 'All Locations'))
    except Exception:
        pass
    return None

def parse_and_validate_date(input_val):
    today = date.today()
    if not input_val:
        return today
        
    s = str(input_val).strip().lower()
    if s in ('today', 'none'):
        resolved = today
    elif s == 'yesterday':
        resolved = today - timedelta(days=1)
    elif s.startswith('-') and s[1:].isdigit():
        resolved = today - timedelta(days=int(s[1:]))
    else:
        try:
            resolved = datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            print(f"[ERROR] Invalid date format '{input_val}'. Please use YYYY-MM-DD, 'yesterday', or 'today'.")
            sys.exit(1)
            
    return resolved

def generate_checkin_sql(batch, output_path):
    """Write companion SQL file for direct execution in Supabase SQL Editor if needed."""
    lines = [
        f"-- OTSi Attendance Check-in Seed: {len(batch)} records",
        f"-- Generated at: {datetime.now().isoformat()}",
        "INSERT INTO attendance_logs (employee_id, attendance_date, check_in_time, check_out_time, check_in_latitude, check_in_longitude, check_in_location, is_wfh, working_hours, status, is_late, location_verified) VALUES"
    ]
    val_rows = []
    for r in batch:
        ci_str = f"'{r['check_in_time']}'" if r['check_in_time'] else "NULL"
        co_str = f"'{r['check_out_time']}'" if r.get('check_out_time') else "NULL"
        lat_str = str(r['check_in_latitude']) if r.get('check_in_latitude') is not None else "NULL"
        lng_str = str(r['check_in_longitude']) if r.get('check_in_longitude') is not None else "NULL"
        loc_str = f"'{r['check_in_location']}'" if r.get('check_in_location') else "NULL"
        is_wfh_str = "TRUE" if r.get('is_wfh') else "FALSE"
        hrs = float(r.get('working_hours', 0.0))
        st = r.get('status', 'present')
        is_late_str = "TRUE" if r.get('is_late') else "FALSE"
        loc_ver_str = "TRUE" if r.get('location_verified') else "FALSE"

        val_rows.append(
            f"    ('{r['employee_id']}', '{r['attendance_date']}', {ci_str}, {co_str}, {lat_str}, {lng_str}, {loc_str}, {is_wfh_str}, {hrs}, '{st}', {is_late_str}, {loc_ver_str})"
        )

    lines.append(",\n".join(val_rows))
    lines.append("""ON CONFLICT (employee_id, attendance_date) DO UPDATE SET
    check_in_time = EXCLUDED.check_in_time,
    check_in_latitude = EXCLUDED.check_in_latitude,
    check_in_longitude = EXCLUDED.check_in_longitude,
    check_in_location = EXCLUDED.check_in_location,
    is_wfh = EXCLUDED.is_wfh,
    status = EXCLUDED.status,
    is_late = EXCLUDED.is_late,
    location_verified = EXCLUDED.location_verified,
    updated_at = CURRENT_TIMESTAMP;
""")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a.lower() for a in sys.argv[1:] if a.startswith('--')]
    force_update = ('--force' in flags or '-f' in flags)
    allow_weekend = ('--include-weekend' in flags or '--weekend' in flags or '-w' in flags)
    is_clear_mode = ('--clear' in flags or '--delete' in flags)

    raw_date = args[0] if args else globals().get('TARGET_DATE')
    target_date = parse_and_validate_date(raw_date)
    today_str = target_date.isoformat()
    day_name = target_date.strftime('%A')
    is_weekend = target_date.weekday() in (5, 6)  # 5=Saturday, 6=Sunday

    print("=" * 65)
    print(f"[OTSi] Attendance Check-in Daily Simulator")
    print(f"Date: {today_str} ({day_name})")
    print(f"Mode: {'Clear records' if is_clear_mode else ('Force overwrite' if force_update else 'Insert new & un-checked-in')}")
    print("=" * 65)

    # Handle --clear / --delete flag
    if is_clear_mode:
        print(f"[ACTION] Purging attendance records for {today_str} ({day_name})...")
        try:
            SupabaseDB.delete('attendance_logs', {'attendance_date': today_str})
            print(f"[OK] Successfully cleared all attendance records for {today_str} from Supabase.")
        except Exception as e:
            print(f"[ERROR] Failed to clear records: {e}")
        return

    allow_holiday = ('--include-holiday' in flags or '--holiday' in flags)

    # Check for Weekend (Saturday/Sunday)
    if is_weekend and not allow_weekend:
        print(f"\n[WEEKEND DETECTED] {today_str} is a {day_name}.")
        print("OTSi operates on a standard Monday-Friday working week.")
        print("By default, no attendance check-in records are generated for weekend non-working days.")
        print("\nTip: If you want to simulate weekend on-call / overtime duty, run:")
        print(f"    python run_checkin_today.py {today_str} --include-weekend\n")
        return

    # Check for Official Company Holiday
    holiday_info = get_company_holiday(today_str)
    if holiday_info and not allow_holiday:
        occ, loc_rem = holiday_info
        print(f"\n[COMPANY HOLIDAY DETECTED] {today_str} ({day_name}) is an official OTSI Company Holiday:")
        print(f"    Occasion : {occ}")
        print(f"    Locations: {loc_rem}")
        print("By default, no attendance check-in records are generated for official company holidays.")
        print("\nTip: If you want to simulate holiday on-call / emergency duty, run:")
        print(f"    python run_checkin_today.py {today_str} --include-holiday\n")
        return
    
    # 1. Fetch active employees
    employees = SupabaseDB.select('employees', 'employee_id, full_name, designation, department, team, status')
    active_employees = [e for e in employees if e.get('status') == 'active']
    print(f'[OK] Found {len(active_employees)} active employees in OTSi database.')
    
    if not active_employees:
        print('[ERROR] No active employees found in table. Please run otsi_org_structure_250.sql first.')
        return

    # 2. Check existing attendance logs for this date
    existing_logs = SupabaseDB.select('attendance_logs', '*', {'attendance_date': today_str})
    existing_map = {log['employee_id']: log for log in existing_logs}
    print(f'[INFO] Found {len(existing_logs)} existing attendance records for {today_str}.')

    # 3. Build realistic check-in distribution
    attendance_batch = []
    stats = {'present': 0, 'wfh': 0, 'late': 0, 'absent': 0, 'skipped': 0}

    # Location presets
    HQ_LAT, HQ_LNG = 17.4418, 78.3809          # OTSi Hyderabad HQ
    CLIENT_LAT, CLIENT_LNG = 17.4320, 78.3720  # Financial District Client Site

    for emp in active_employees:
        emp_id = emp['employee_id']
        existing = existing_map.get(emp_id)

        # Skip if already checked in and not forcing overwrite
        if existing and existing.get('check_in_time') and not force_update:
            stats['skipped'] += 1
            continue

        # ~94% Attendance rate (6% absent/on-leave)
        is_attending = random.random() < 0.94

        if not is_attending:
            # Marked absent for today
            attendance_batch.append({
                'employee_id': emp_id,
                'attendance_date': today_str,
                'check_in_time': None,
                'check_out_time': None,
                'check_in_latitude': None,
                'check_in_longitude': None,
                'check_in_location': None,
                'is_wfh': False,
                'working_hours': 0.0,
                'status': 'absent',
                'is_late': False,
                'location_verified': True
            })
            stats['absent'] += 1
            continue

        # Location assignment: 70% OTSi HQ, 15% Client Site, 15% WFH
        loc_choice = random.choices(['HQ', 'CLIENT', 'WFH'], weights=[70, 15, 15], k=1)[0]
        
        if loc_choice == 'HQ':
            loc_name = 'OTSi Hyderabad HQ'
            lat = round(HQ_LAT + random.uniform(-0.0006, 0.0006), 6)
            lng = round(HQ_LNG + random.uniform(-0.0006, 0.0006), 6)
            is_wfh = False
        elif loc_choice == 'CLIENT':
            loc_name = 'Client Site - Financial District'
            lat = round(CLIENT_LAT + random.uniform(-0.0008, 0.0008), 6)
            lng = round(CLIENT_LNG + random.uniform(-0.0008, 0.0008), 6)
            is_wfh = False
        else:
            loc_name = 'WFH'
            lat = None
            lng = None
            is_wfh = True

        # Check-in time simulation (Arrival in IST, stored as UTC)
        # Standard: 08:35 to 09:28 AM IST  -> UTC 03:05 to 03:58
        # Late (~8% of arrivals): 09:31 to 10:15 AM IST -> UTC 04:01 to 04:45
        is_late_arrival = random.random() < 0.08
        if is_late_arrival:
            ci_utc_hour = 4
            ci_utc_min = random.randint(1, 45) # 09:31 to 10:15 AM IST
            is_late = True
        else:
            ci_utc_hour = 3
            ci_utc_min = random.randint(5, 58) # 08:35 to 09:28 AM IST
            is_late = False

        ci_utc_sec = random.randint(0, 59)
        ci_dt = datetime(target_date.year, target_date.month, target_date.day, ci_utc_hour, ci_utc_min, ci_utc_sec, tzinfo=timezone.utc)
        
        # Status calculation
        if is_wfh:
            status = 'wfh'
            stats['wfh'] += 1
        elif is_late:
            status = 'late'
            stats['late'] += 1
        else:
            status = 'present'
            stats['present'] += 1

        attendance_batch.append({
            'employee_id': emp_id,
            'attendance_date': today_str,
            'check_in_time': ci_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'check_out_time': existing.get('check_out_time') if existing else None,
            'check_in_latitude': lat,
            'check_in_longitude': lng,
            'check_in_location': loc_name,
            'is_wfh': is_wfh,
            'working_hours': float(existing.get('working_hours', 0.0)) if existing else 0.0,
            'status': status,
            'is_late': is_late,
            'location_verified': True
        })

    # 4. Generate companion SQL file
    sql_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkin_today.sql")
    generate_checkin_sql(attendance_batch, sql_path)
    print(f"[SQL] Companion SQL file created: {sql_path}")

    # 5. Push to Supabase via batch upsert
    if attendance_batch:
        print(f"[SYNC] Inserting {len(attendance_batch)} attendance records into Supabase...")
        chunk_size = 50
        inserted_total = 0
        rls_error = False

        for i in range(0, len(attendance_batch), chunk_size):
            chunk = attendance_batch[i:i + chunk_size]
            try:
                SupabaseDB.upsert_many('attendance_logs', chunk, on_conflict='employee_id,attendance_date')
                inserted_total += len(chunk)
            except Exception as e:
                err_str = str(e)
                if '42501' in err_str or 'row-level security' in err_str.lower():
                    rls_error = True
                    break
                else:
                    print(f"[WARNING] Chunk {i // chunk_size + 1} error: {e}")

        if rls_error:
            print("\n" + "! " * 35)
            print("[NOTICE] Supabase Row Level Security (RLS) is active on 'attendance_logs'.")
            print("To allow API script inserts, run this 1-line query in Supabase SQL Editor:")
            print("\n    ALTER TABLE attendance_logs DISABLE ROW LEVEL SECURITY;\n")
            print(f"Alternatively, you can run the generated SQL migration file directly:")
            print(f"    {sql_path}")
            print("! " * 35 + "\n")
        else:
            print(f"[OK] Successfully synced {inserted_total} check-in records to Supabase!")

    print("\n" + "-" * 40)
    print("Attendance Check-in Summary:")
    print(f"   [+] Present (Office / Client Site): {stats['present']}")
    print(f"   [+] WFH:                            {stats['wfh']}")
    print(f"   [+] Late:                           {stats['late']}")
    print(f"   [-] Absent / Leave:                 {stats['absent']}")
    if stats['skipped'] > 0:
        print(f"   [>] Already Checked-in (Skipped):  {stats['skipped']} (use --force to overwrite)")
    print("-" * 40)
    print("=== Check-in Simulation Completed ===")

if __name__ == '__main__':
    main()
