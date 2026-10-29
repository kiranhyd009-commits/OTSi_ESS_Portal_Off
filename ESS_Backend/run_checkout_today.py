#!/usr/bin/env python3
"""
OTSi ESS Portal - Daily Attendance Check-out Generator / Simulator
Simulates realistic checkout times and calculated working hours for all checked-in employees.
Supports testing and temporary daily data generation for non-live portal demonstration.

Usage:
    python run_checkout_today.py                    # Check out all checked-in employees for today
    python run_checkout_today.py yesterday          # Run for yesterday
    python run_checkout_today.py 2026-10-27         # Run for specific date
    python run_checkout_today.py --force            # Re-calculate/overwrite existing checkouts
    python run_checkout_today.py --strict-time      # Only check out if checkout time is in the past
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

def parse_iso_datetime(time_str):
    if not time_str:
        return None
    cleaned = time_str.replace('Z', '').split('+')[0]
    try:
        return datetime.fromisoformat(cleaned)
    except Exception:
        pass
    try:
        return datetime.strptime(cleaned.split('.')[0], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        pass
    return None

def generate_checkout_sql(batch, output_path):
    """Write companion SQL file for direct execution in Supabase SQL Editor if needed."""
    lines = [
        f"-- OTSi Attendance Check-out Seed: {len(batch)} records",
        f"-- Generated at: {datetime.now().isoformat()}",
        "INSERT INTO attendance_logs (employee_id, attendance_date, check_in_time, check_out_time, check_in_latitude, check_in_longitude, check_in_location, is_wfh, working_hours, status, is_late, location_verified) VALUES"
    ]
    val_rows = []
    for r in batch:
        ci_str = f"'{r['check_in_time']}'" if r.get('check_in_time') else "NULL"
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
    check_out_time = EXCLUDED.check_out_time,
    working_hours = EXCLUDED.working_hours,
    status = EXCLUDED.status,
    updated_at = CURRENT_TIMESTAMP;
""")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a.lower() for a in sys.argv[1:] if a.startswith('--')]
    force_update = ('--force' in flags or '-f' in flags)
    strict_time = ('--strict-time' in flags)
    allow_weekend = ('--include-weekend' in flags or '--weekend' in flags or '-w' in flags)
    is_clear_mode = ('--clear' in flags or '--delete' in flags)

    raw_date = args[0] if args else globals().get('TARGET_DATE')
    target_date = parse_and_validate_date(raw_date)
    today_str = target_date.isoformat()
    day_name = target_date.strftime('%A')
    is_weekend = target_date.weekday() in (5, 6)
    is_today = (target_date == date.today())
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    print("=" * 65)
    print(f"[OTSi] Attendance Check-out Daily Simulator")
    print(f"Date: {today_str} ({day_name})")
    print(f"Mode: {'Clear records' if is_clear_mode else ('Force recalculate all' if force_update else 'Check out pending checked-in employees')}")
    print(f"Policy: {'Strict (skip future checkouts)' if strict_time else 'Simulate Completed Shifts (Demo Mode)'}")
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
        print("No checkout processing needed for weekend non-working days.")
        print("\nTip: If you specifically ran a weekend check-in simulation, pass the flag:")
        print(f"    python run_checkout_today.py {today_str} --include-weekend\n")
        return

    # Check for Official Company Holiday
    holiday_info = get_company_holiday(today_str)
    if holiday_info and not allow_holiday:
        occ, loc_rem = holiday_info
        print(f"\n[COMPANY HOLIDAY DETECTED] {today_str} ({day_name}) is an official OTSI Company Holiday:")
        print(f"    Occasion : {occ}")
        print(f"    Locations: {loc_rem}")
        print("No checkout processing needed for official company holidays.")
        print("\nTip: If you specifically ran a holiday simulation, pass:")
        print(f"    python run_checkout_today.py {today_str} --include-holiday\n")
        return

    # 1. Fetch all attendance logs for target date
    logs = SupabaseDB.select('attendance_logs', '*', {'attendance_date': today_str})
    print(f"[INFO] Found {len(logs)} attendance logs for {today_str}.")

    # 2. Filter records eligible for check-out
    eligible = []
    for log in logs:
        if not log.get('check_in_time'):
            continue
        if log.get('check_out_time') and not force_update:
            continue
        eligible.append(log)

    print(f"[INFO] Eligible employees to check out: {len(eligible)}")

    if not eligible:
        print("[OK] All checked-in employees already have checkout times recorded. Use --force to re-generate.")
        return

    # 3. Simulate realistic checkout times and working hours
    updated_batch = []
    stats = {'full_day': 0, 'half_day': 0, 'skipped_future': 0, 'total_hours': 0.0}

    for log in eligible:
        ci_str = log['check_in_time']
        ci_dt = parse_iso_datetime(ci_str)

        if not ci_dt:
            continue

        # Half-day simulation (~3% of employees leave early)
        is_half_day = random.random() < 0.03

        if is_half_day:
            co_hours_add = 4
            co_mins_add = random.randint(10, 35)
        else:
            # Standard shift: 8h 15m to 9h 30m
            co_hours_add = random.choice([8, 8, 9])
            if co_hours_add == 8:
                co_mins_add = random.randint(15, 55)
            else:
                co_mins_add = random.randint(5, 30)

        co_secs_add = random.randint(0, 59)
        co_dt = ci_dt + timedelta(hours=co_hours_add, minutes=co_mins_add, seconds=co_secs_add)

        # In strict mode, skip if checkout would be in the future for today
        if strict_time and is_today and co_dt > now_utc:
            stats['skipped_future'] += 1
            continue

        # Calculate exact working hours
        delta = co_dt - ci_dt
        working_hours = round(delta.total_seconds() / 3600.0, 2)
        stats['total_hours'] += working_hours

        # Update status if half day
        status = log.get('status', 'present')
        if working_hours < 5.0:
            status = 'half_day'
            stats['half_day'] += 1
        else:
            stats['full_day'] += 1

        co_str_formatted = co_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        updated_batch.append({
            'employee_id': log['employee_id'],
            'attendance_date': today_str,
            'check_in_time': log['check_in_time'],
            'check_out_time': co_str_formatted,
            'check_in_latitude': log.get('check_in_latitude'),
            'check_in_longitude': log.get('check_in_longitude'),
            'check_in_location': log.get('check_in_location'),
            'is_wfh': log.get('is_wfh', False),
            'working_hours': working_hours,
            'status': status,
            'is_late': log.get('is_late', False),
            'location_verified': log.get('location_verified', True)
        })

    # 4. Write companion SQL file
    sql_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkout_today.sql")
    generate_checkout_sql(updated_batch, sql_path)
    print(f"[SQL] Companion SQL file created: {sql_path}")

    # 5. Push batch upsert to Supabase
    if updated_batch:
        print(f"[SYNC] Updating {len(updated_batch)} check-out records in Supabase...")
        chunk_size = 50
        updated_total = 0
        rls_error = False

        for i in range(0, len(updated_batch), chunk_size):
            chunk = updated_batch[i:i + chunk_size]
            try:
                SupabaseDB.upsert_many('attendance_logs', chunk, on_conflict='employee_id,attendance_date')
                updated_total += len(chunk)
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
            print("To allow API script updates, run this 1-line query in Supabase SQL Editor:")
            print("\n    ALTER TABLE attendance_logs DISABLE ROW LEVEL SECURITY;\n")
            print(f"Alternatively, you can run the generated SQL migration file directly:")
            print(f"    {sql_path}")
            print("! " * 35 + "\n")
        else:
            print(f"[OK] Successfully synced {updated_total} check-out records to Supabase!")

    avg_hours = round(stats['total_hours'] / max(1, len(updated_batch)), 2)
    print("\n" + "-" * 40)
    print("Attendance Check-out Summary:")
    print(f"   [+] Full Shifts Completed (8.2h - 9.5h): {stats['full_day']}")
    print(f"   [+] Half-Day Checkouts:                   {stats['half_day']}")
    print(f"   [+] Average Working Hours:                {avg_hours} hrs")
    if stats['skipped_future'] > 0:
        print(f"   [>] Skipped (Future Checkouts):           {stats['skipped_future']} (run without --strict-time to complete demo shifts)")
    print("-" * 40)
    print("=== Check-out Simulation Completed ===")

if __name__ == '__main__':
    main()
