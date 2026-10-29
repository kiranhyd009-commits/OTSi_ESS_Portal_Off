"""Utility functions for business logic"""
import math
from datetime import datetime, date, timedelta, timezone
from database import SupabaseDB
import logging
import smtplib
import threading
from email.mime.text import MIMEText
import os

logger = logging.getLogger(__name__)


class LocationUtils:
    """Location-based utilities"""
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in meters using Haversine formula"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def is_within_office(latitude: float, longitude: float, office_lat: float, 
                        office_lng: float, radius_m: float, office_locations: list | None = None,
                        metro_radius_m: float = 20000) -> bool:
        """Check if coordinates are within any office geofence or city metro ISP network radius"""
        # 1. Strict campus radius check
        if office_locations:
            for loc in office_locations:
                d = LocationUtils.calculate_distance(latitude, longitude, loc['lat'], loc['lng'])
                if d <= loc.get('radius', radius_m):
                    return True
        else:
            distance = LocationUtils.calculate_distance(latitude, longitude, office_lat, office_lng)
            if distance <= radius_m:
                return True

        # 2. Metro network check: allows office desktop PCs / Ethernet with city-level ISP geolocation (e.g. Hyderabad centroid ~10.9km)
        locs = office_locations if office_locations else [{'lat': office_lat, 'lng': office_lng}]
        min_dist = min(LocationUtils.calculate_distance(latitude, longitude, loc['lat'], loc['lng']) for loc in locs)
        return min_dist <= metro_radius_m


class AttendanceUtils:
    """Attendance-related utilities"""
    
    @staticmethod
    def get_attendance_status(check_in: datetime, check_out: datetime | None = None, is_wfh: bool = False) -> str:
        """Determine attendance status"""
        if is_wfh:
            return 'wfh'
        
        if not check_in:
            return 'absent'
        
        # Convert check_in (UTC) to IST (+05:30) and check if late (office starts at 09:30 IST)
        if isinstance(check_in, datetime):
            ist_check_in = check_in + timedelta(hours=5, minutes=30)
            check_in_time = ist_check_in.time()
        elif isinstance(check_in, str):
            dt = datetime.fromisoformat(check_in.replace('Z', ''))
            ist_check_in = dt + timedelta(hours=5, minutes=30)
            check_in_time = ist_check_in.time()
        else:
            check_in_time = check_in
            
        OFFICE_START = datetime.strptime("09:30", "%H:%M").time()
        
        if check_in_time > OFFICE_START:
            return 'late'
        
        return 'present'
    
    @staticmethod
    def calculate_working_hours(check_in: datetime | None, check_out: datetime | None = None) -> float:
        """Calculate working hours"""
        if not check_in:
            return 0.0
        
        if not check_out:
            check_out = datetime.now(timezone.utc)
            
        if check_in.tzinfo is None:
            check_in = check_in.replace(tzinfo=timezone.utc)
        if check_out.tzinfo is None:
            check_out = check_out.replace(tzinfo=timezone.utc)
        
        delta = check_out - check_in
        hours = delta.total_seconds() / 3600
        return round(hours, 2)
    
    @staticmethod
    def get_working_hours_today(employee_id: str, office_start: str = "09:00", 
                               office_end: str = "18:00") -> dict:
        """Get working hours for today"""
        today = date.today()
        
        record = SupabaseDB.select_one('attendance_logs', {
            'employee_id': employee_id,
            'attendance_date': today.isoformat()
        })
        
        if not record:
            return {'status': 'absent', 'hours': 0.0, 'check_in': None, 'check_out': None}
        
        check_in = record['check_in_time']
        check_out = record['check_out_time']
        is_wfh = record['is_wfh']
        
        status = AttendanceUtils.get_attendance_status(check_in, check_out, is_wfh)
        hours = AttendanceUtils.calculate_working_hours(
            datetime.fromisoformat(check_in) if check_in else None,
            datetime.fromisoformat(check_out) if check_out else None
        )
        
        return {
            'status': status,
            'hours': hours,
            'check_in': check_in,
            'check_out': check_out,
            'is_wfh': is_wfh
        }
    
    @staticmethod
    def fill_missing_attendance(employee_id: str, records: list, start_dt: date, end_dt: date) -> list:
        """Fill in missing weekdays as 'absent' records between start_dt and end_dt."""
        record_map = {r['attendance_date']: r for r in records}
        filled_records = []
        
        # Fetch dynamic holidays from database
        try:
            holidays_data = SupabaseDB.select('holidays')
            holiday_dates = {h['holiday_date'] for h in holidays_data}
        except Exception as e:
            logger.error(f"Failed to fetch holidays for gap filling: {str(e)}")
            holiday_dates = set()
        
        current = start_dt
        while current <= end_dt:
            date_str = current.isoformat()
            
            if date_str in record_map:
                filled_records.append(record_map[date_str])
            else:
                # If no record exists, check if it's a weekday and not a holiday
                is_weekend = current.weekday() in [5, 6] # 5 = Saturday, 6 = Sunday
                is_holiday = date_str in holiday_dates
                
                # Only insert 'absent' if it's a regular working day
                if not is_weekend and not is_holiday:
                    synthetic_record = {
                        'employee_id': employee_id,
                        'attendance_date': date_str,
                        'check_in_time': None,
                        'check_out_time': None,
                        'check_in_location': None,
                        'is_wfh': False,
                        'working_hours': 0.0,
                        'status': 'absent',
                        'is_late': False,
                        'location_verified': True,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    filled_records.append(synthetic_record)
            
            current += timedelta(days=1)
            
        return filled_records
    @staticmethod
    def get_attendance_stats(employee_id: str, month: int | None = None, year: int | None = None) -> dict:
        """Get attendance statistics for a month"""
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year
        
        filters = {
            'employee_id': employee_id,
            'attendance_date': (
                'gte',
                f"{year}-{month:02d}-01"
            )
        }
        
        db_records = SupabaseDB.select('attendance_logs', "*", filters)
        
        import calendar
        _, last_day = calendar.monthrange(year, month)
        start_dt = date(year, month, 1)
        end_dt = min(date(year, month, last_day), date.today())
        
        records = AttendanceUtils.fill_missing_attendance(employee_id, db_records, start_dt, end_dt)
        
        stats = {
            'present': 0,
            'wfh': 0,
            'on_leave': 0,
            'half_day': 0,
            'correction': 0,
            'total_hours': 0.0
        }
        
        for record in records:
            status = record['status']
            if status in ['present', 'late']:
                stats['present'] += 1
            elif status == 'wfh':
                stats['wfh'] += 1
            elif status == 'half_day':
                stats['half_day'] += 1
            
            if record['working_hours']:
                stats['total_hours'] += record['working_hours']
                
        # Calculate ON LEAVE for current month
        try:
            leave_apps = SupabaseDB.select('leave_applications', "*", {'employee_id': employee_id, 'status': 'approved'})
            on_leave_days = set()
            for app in leave_apps:
                s_date = datetime.strptime(app['start_date'], '%Y-%m-%d').date()
                e_date = datetime.strptime(app['end_date'], '%Y-%m-%d').date()
                
                curr = s_date
                while curr <= e_date:
                    if curr.month == month and curr.year == year:
                        on_leave_days.add(curr)
                    curr += timedelta(days=1)
            stats['on_leave'] = len(on_leave_days)
        except Exception as e:
            logger.error(f"Error calculating on_leave stats: {e}")
            
        # Calculate CORRECTION for current month
        try:
            corrections = SupabaseDB.select('attendance_correction_requests', "*", {'employee_id': employee_id})
            corr_count = 0
            for c in corrections:
                c_date_str = c.get('attendance_date')
                if c_date_str:
                    try:
                        c_date = datetime.strptime(c_date_str, '%Y-%m-%d').date()
                        if c_date.month == month and c_date.year == year:
                            corr_count += 1
                    except:
                        pass
            stats['correction'] = corr_count
        except Exception as e:
            logger.error(f"Error calculating correction stats: {e}")
        
        stats['total_hours'] = round(stats['total_hours'], 2)
        return stats


class LeaveUtils:
    """Leave-related utilities"""
    
    # Canonical mapping from leave_type value → leave_balance column name
    LEAVE_COLUMN_MAP = {
        'casual': 'casual_leave',
        'casual_leave': 'casual_leave',
        'casual leave': 'casual_leave',
        'csl': 'casual_leave',
        'casual, sick leave': 'casual_leave',
        'sick': 'sick_leave',
        'sick_leave': 'sick_leave',
        'sick leave': 'sick_leave',
        'earned': 'earned_leave',
        'earned_leave': 'earned_leave',
        'earned leave': 'earned_leave',
        'el': 'earned_leave',
        'bereavement': 'bereavement_leave',
        'bereavement_leave': 'bereavement_leave',
        'bereavement leave': 'bereavement_leave',
        'marriage': 'marriage_leave',
        'marriage_leave': 'marriage_leave',
        'marriage leave': 'marriage_leave',
        'lop': 'lop_leave',
        'lop_leave': 'lop_leave',
        'lop leave': 'lop_leave',
    }
    
    # Leave types that don't deduct from a balance column
    NON_BALANCE_TYPES = {'permission', 'wfh', 'half_day', 'paternity', 'optional_holiday'}
    
    @staticmethod
    def get_leave_column(leave_type: str):
        """Return the balance column name for a leave type, or None if not applicable."""
        if not leave_type:
            return None
        return LeaveUtils.LEAVE_COLUMN_MAP.get(leave_type.lower().strip())
    
    @staticmethod
    def calculate_leave_days(start_date: date, end_date: date) -> float:
        """Calculate number of leave days (excluding weekends and holidays)"""
        current = start_date
        days = 0
        
        try:
            holidays_data = SupabaseDB.select('holidays')
            holiday_dates = {h['holiday_date'] for h in holidays_data}
        except Exception as e:
            logger.error(f"Failed to fetch holidays for calculate_leave_days: {str(e)}")
            holiday_dates = set()
        
        while current <= end_date:
            # 5 = Saturday, 6 = Sunday
            if current.weekday() < 5 and current.isoformat() not in holiday_dates:
                days += 1
            current += timedelta(days=1)
        
        return float(days)
    
    @staticmethod
    def get_leave_balance(employee_id: str) -> dict:
        """Get leave balance for an employee"""
        balance = SupabaseDB.select_one('leave_balance', {'employee_id': employee_id})
        
        if not balance:
            return {
                'casual_leave': 0,
                'sick_leave': 0,
                'earned_leave': 0,
                'bereavement_leave': 0,
                'marriage_leave': 0,
                'lop_leave': 0
            }
        
        return {
            'casual_leave': balance['casual_leave'],
            'sick_leave': balance['sick_leave'],
            'earned_leave': balance['earned_leave'],
            'bereavement_leave': balance['bereavement_leave'],
            'marriage_leave': balance['marriage_leave'],
            'lop_leave': balance['lop_leave']
        }
    
    @staticmethod
    def deduct_leave(employee_id: str, leave_type: str, days: float) -> bool:
        """Deduct leave from balance with cascading adjustment rules."""
        if leave_type.lower() in LeaveUtils.NON_BALANCE_TYPES:
            return True
        
        balance = SupabaseDB.select_one('leave_balance', {'employee_id': employee_id})
        if not balance:
            return False
            
        updates = {}
        remaining = days
        
        # Helper to deduct from a column
        def deduct_from_col(col_name, amount):
            current = balance.get(col_name, 0) or 0
            if col_name in updates:
                current = updates[col_name]
            
            if current >= amount:
                new_val = current - amount
                updates[col_name] = new_val if col_name == 'earned_leave' else int(new_val)
                return 0.0
            else:
                updates[col_name] = 0.0 if col_name == 'earned_leave' else 0
                return amount - current

        lt = leave_type.lower()
        if lt == 'casual':
            # Deduct from casual_leave first, then sick_leave, then lop
            remaining = deduct_from_col('casual_leave', remaining)
            if remaining > 0:
                remaining = deduct_from_col('sick_leave', remaining)
            if remaining > 0:
                current_lop = balance.get('lop_leave', 0) or 0
                updates['lop_leave'] = int(current_lop + remaining)
                
        elif lt == 'earned':
            # Deduct from earned_leave, then casual_leave, then sick_leave, then lop
            remaining = deduct_from_col('earned_leave', remaining)
            if remaining > 0:
                remaining = deduct_from_col('casual_leave', remaining)
            if remaining > 0:
                remaining = deduct_from_col('sick_leave', remaining)
            if remaining > 0:
                current_lop = balance.get('lop_leave', 0) or 0
                updates['lop_leave'] = int(current_lop + remaining)
                
        else:
            # Standard single column deduction (e.g. bereavement, marriage)
            column = LeaveUtils.get_leave_column(leave_type)
            if column:
                remaining = deduct_from_col(column, remaining)
                if remaining > 0:
                    current_lop = balance.get('lop_leave', 0) or 0
                    updates['lop_leave'] = int(current_lop + remaining)
            else:
                logger.warning(f"deduct_leave: unknown leave type '{leave_type}' — skipping deduction")
                return False
                
        if updates:
            SupabaseDB.update('leave_balance', 
                             {'employee_id': employee_id},
                             updates)
            logger.info(f"deduct_leave: employee {employee_id} leave updates: {updates}")
            
        return True


class TimesheetUtils:
    """Timesheet-related utilities"""
    
    @staticmethod
    def get_week_dates(date_obj: date | None = None):
        """Get week start and end dates"""
        if date_obj is None:
            date_obj = date.today()
        
        # Monday = 0, Sunday = 6
        start = date_obj - timedelta(days=date_obj.weekday())
        end = start + timedelta(days=4)  # Friday
        
        return start, end
    
    @staticmethod
    def calculate_timesheet_hours(timesheet_id: int) -> float:
        """Calculate total hours for a timesheet"""
        entries = SupabaseDB.select('timesheet_entries', '*', {'timesheet_id': timesheet_id})
        
        total_hours = sum(entry['hours_worked'] for entry in entries if entry['hours_worked'])
        return round(total_hours, 2)


class NotificationUtils:
    """Notification-related utilities"""
    
    @staticmethod
    def send_email_async(to_email: str, subject: str, body: str):
        """Send email asynchronously to avoid blocking"""
        def _send():
            try:
                smtp_server = os.getenv("SMTP_SERVER", "smtp.sendgrid.net")
                smtp_port = int(os.getenv("SMTP_PORT", 587))
                smtp_user = os.getenv("SMTP_USERNAME", "apikey")
                smtp_pass = os.getenv("SMTP_PASSWORD", "")
                from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@otsi-ess.com")
                
                if not smtp_pass:
                    # Skip if SMTP not configured
                    return
                
                msg = MIMEText(body)
                msg['Subject'] = subject
                msg['From'] = from_email
                msg['To'] = to_email
                
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
                server.quit()
            except Exception as e:
                logger.error(f"Failed to send email to {to_email}: {str(e)}")
                
        threading.Thread(target=_send, daemon=True).start()

    @staticmethod
    def create_notification(employee_id: str, title: str, message: str, 
                          notification_type: str = 'info', action_url: str | None = None) -> dict | None:
        """Create a notification and optionally send email"""
        notification_data = {
            'employee_id': employee_id,
            'title': title,
            'message': message,
            'type': notification_type,
            'is_read': False,
            'action_url': action_url,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Look up employee email
        emp = SupabaseDB.select_one('employees', {'employee_id': employee_id})
        if emp and emp.get('email'):
            NotificationUtils.send_email_async(
                emp['email'],
                f"ESS Portal: {title}",
                f"Hello {emp.get('full_name', 'Employee')},\n\n{message}\n\nThank you,\nOTSi ESS Portal"
            )
            
        return SupabaseDB.insert('notifications', notification_data)
    
    @staticmethod
    def get_unread_count(employee_id: str) -> int:
        """Get count of unread notifications"""
        return SupabaseDB.count('notifications', {
            'employee_id': employee_id,
            'is_read': False
        })


from typing import Optional

def log_audit(employee_id: str, action: str, entity_type: str, entity_id: Optional[int] = None,
             old_values: Optional[dict] = None, new_values: Optional[dict] = None, ip_address: Optional[str] = None):
    """Log audit trail"""
    from flask import request as flask_request
    
    audit_data = {
        'employee_id': employee_id,
        'action': action,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'old_values': old_values,
        'new_values': new_values,
        'ip_address': ip_address or flask_request.remote_addr,
        'user_agent': flask_request.user_agent.string,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    try:
        SupabaseDB.insert('audit_logs', audit_data)
    except Exception as e:
        logger.error(f"Failed to log audit: {str(e)}")


class EmailService:
    """Service for sending emails via SMTP"""
    
    @staticmethod
    def send_password_reset_email(to_email: str, reset_link: str) -> bool:
        """Sends a password reset email."""
        smtp_host = os.getenv('SMTP_HOST')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USERNAME')
        smtp_pass = os.getenv('SMTP_PASSWORD')
        
        if smtp_host is None or smtp_user is None or smtp_pass is None:
            logger.warning("SMTP credentials are not fully configured. Email not sent.")
            return False
            
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "OTSi ESS Portal - Password Reset"
            msg["From"] = smtp_user
            msg["To"] = to_email
            
            text = (
                f"Hi,\n\n"
                f"We received a request to reset your OTSi ESS Portal password.\n\n"
                f"Click the link below to reset it (expires in 1 hour):\n{reset_link}\n\n"
                f"If you didn't request this, no action is needed — your password remains unchanged.\n\n"
                f"— OTSi ESS Portal Team"
            )
            html = f"""\
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f6f6f6;font-family:Arial,sans-serif;">
  <div style="max-width:520px;margin:40px auto;background:#ffffff;border-radius:8px;padding:40px;border:1px solid #e0e0e0;">
    <p style="margin:0 0 4px;font-size:13px;color:#888;font-weight:600;letter-spacing:1px;text-transform:uppercase;">OTSi ESS Portal</p>
    <h2 style="margin:0 0 16px;font-size:20px;color:#1a1a1a;">Reset your password</h2>
    <p style="margin:0 0 28px;font-size:14px;color:#555;line-height:1.7;">
      We received a request to reset the password for your account. Click the button below to choose a new password. This link expires in 1 hour.
    </p>
    <span style="display:inline-block;">
      <a href="{reset_link}" target="_blank"
         style="display:inline-block;padding:10px 20px;background:#2563eb;color:#ffffff;
                font-size:14px;font-weight:600;text-decoration:none;border-radius:6px;
                white-space:nowrap;">Reset Password</a>
    </span>
    <hr style="border:none;border-top:1px solid #eeeeee;margin:32px 0;">
    <p style="margin:0 0 8px;font-size:12px;color:#999;">If the button doesn't work, copy and paste this link:</p>
    <p style="margin:0;font-size:12px;word-break:break-all;">
      <a href="{reset_link}" style="color:#2563eb;">{reset_link}</a>
    </p>
    <p style="margin:24px 0 0;font-size:12px;color:#bbb;">If you didn't request this, you can safely ignore this email.</p>
  </div>
</body>
</html>"""
            
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            msg.attach(part1)
            msg.attach(part2)
            
            # Connect using STARTTLS (port 587)
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Password reset email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False


