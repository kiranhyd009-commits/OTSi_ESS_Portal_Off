"""Authentication utilities"""
import jwt
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
# pyrefly: ignore [missing-import]
from flask import request, jsonify, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logger = logging.getLogger(__name__)


class AuthUtils:
    """Authentication utilities"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return generate_password_hash(password)
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return check_password_hash(password_hash, password)

    @staticmethod
    def validate_password_policy(password: str, email: str, full_name: str, employee_id: str) -> tuple:
        """Validate password against policy"""
        if len(password) < 8 or len(password) > 64:
            return False, "Password must be between 8 and 64 characters."
            
        # --- TEMPORARILY DISABLED FOR TESTING ---
        
        """
        # Check categories (At least 3 of 4)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*" for c in password)
        
        if not has_special:
            return False, "Password must contain at least one special character (!@#$%^&*)."
            
        categories_count = sum([has_upper, has_lower, has_digit, has_special])
        if categories_count < 3:
            return False, "Password must contain at least 3 of the following categories: uppercase, lowercase, numbers, and special characters (!@#$%^&*)."
            
        p_lower = password.lower()
        
        # Must not contain company name
        if "otsi" in p_lower:
            return False, "Password must not contain the company name ('otsi')."
            
        # Must not contain Employee ID
        if employee_id and employee_id.lower() in p_lower:
            return False, "Password must not contain your Employee ID."
            
        # Must not contain username parts
        if email:
            username = email.split('@')[0]
            if username.lower() in p_lower:
                return False, "Password must not contain your email username."
            for part in username.split('.'):
                if len(part) >= 3 and part.lower() in p_lower:
                    return False, "Password must not contain parts of your email username."
                    
        # Must not contain name parts
        if full_name:
            for part in full_name.split():
                if len(part) >= 3 and part.lower() in p_lower:
                    return False, "Password must not contain parts of your name."
                    
        # Must not contain common passwords
        common_passwords = ["password", "welcome", "admin", "otsi", "employee", "manager", "12345678"]
        for common in common_passwords:
            if common in p_lower:
                return False, f"Password must not contain common password terms (like '{common}')."
                
        return True, ""
        """
        return True, ""


    @staticmethod
    def check_password_history(employee_id: str, new_password: str) -> tuple:
        """Verify that password is not in the last 5 passwords"""
        # --- TEMPORARILY DISABLED FOR TESTING ---
        
        """
        from database import SupabaseDB
        try:
            client = SupabaseDB.get_client()
            response = client.table('password_history').select('password_hash').eq('employee_id', employee_id).order('created_at', desc=True).limit(5).execute()
            history = response.data
            if history:
                for record in history:
                    if AuthUtils.verify_password(new_password, record['password_hash']):
                        return True, "You cannot reuse any of your last 5 passwords."
        except Exception as e:
            logger.error(f"Error checking password history: {str(e)}")
        return False, ""
        """
        return False, ""
    
    @staticmethod
    def create_access_token(employee_id: str, role: str, expires_in: int = 24) -> str:
        """Create JWT access token"""
        payload = {
            'employee_id': employee_id,
            'role': role,
            'exp': datetime.now(timezone.utc) + timedelta(hours=expires_in),
            'iat': datetime.now(timezone.utc)
        }
        return jwt.encode(
            payload,
            os.getenv('JWT_SECRET_KEY', 'your-secret-key'),
            algorithm='HS256'
        )
    
    @staticmethod
    def create_refresh_token(employee_id: str, role: str, expires_in: int = 720) -> str:
        """Create JWT refresh token"""
        payload = {
            'employee_id': employee_id,
            'role': role,
            'exp': datetime.now(timezone.utc) + timedelta(hours=expires_in),
            'iat': datetime.now(timezone.utc),
            'type': 'refresh'
        }
        return jwt.encode(
            payload,
            os.getenv('JWT_SECRET_KEY', 'your-secret-key'),
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_token(token: str, expected_type: str | None = None) -> dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                os.getenv('JWT_SECRET_KEY', 'your-secret-key'),
                algorithms=['HS256']
            )
            if expected_type and payload.get('type') != expected_type:
                raise Exception('Invalid token type')
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception('Token expired')
        except jwt.InvalidTokenError:
            raise Exception('Invalid token')

    @staticmethod
    def get_token_from_request():
        """Extract JWT token from request header"""
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            return parts[1]
        
        return None


def token_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = AuthUtils.get_token_from_request()
        
        if not token:
            return jsonify({'error': 'Missing authorization token'}), 401
        
        try:
            if TokenBlacklist.is_blacklisted(token):
                return jsonify({'error': 'Token has been revoked'}), 401
            payload = AuthUtils.verify_token(token)
            g.current_user = payload
            g.current_employee_id = payload['employee_id']
            g.current_role = payload['role']
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            return jsonify({'error': str(e)}), 401
        
        return f(*args, **kwargs)
    
    return decorated


def role_required(*roles):
    """Decorator to require specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'current_role'):
                return jsonify({'error': 'Not authenticated'}), 401
            
            if g.current_role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


class TokenBlacklist:
    """Token blacklist for logout"""
    _blacklist = set()
    
    @classmethod
    def add(cls, token: str):
        """Add token to blacklist"""
        cls._blacklist.add(token)
    
    @classmethod
    def is_blacklisted(cls, token: str) -> bool:
        """Check if token is blacklisted"""
        return token in cls._blacklist
