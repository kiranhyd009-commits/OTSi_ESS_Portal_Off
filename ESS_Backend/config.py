import os
from datetime import timedelta

class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
    
    # SMTP Settings (for Email Notifications)
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.sendgrid.net")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "apikey")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@otsi-ess.com")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://your-project.supabase.co')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'your-supabase-key')
    SUPABASE_SCHEMA = os.getenv('SUPABASE_SCHEMA', 'public')
    
    # CORS Configuration
    CORS_HEADERS = 'Content-Type'
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    # MFA feature flag
    MFA_ENABLED = os.getenv('MFA_ENABLED', 'true').strip().lower() in ('1', 'true', 'yes', 'on')
    
    # Office Location (OTSi Hyderabad HQ - Building H02, Phoenix Infocity SEZ)
    OFFICE_LAT = float(os.getenv('OFFICE_LAT', '17.4418'))
    OFFICE_LNG = float(os.getenv('OFFICE_LNG', '78.3809'))
    OFFICE_RADIUS_M = int(os.getenv('OFFICE_RADIUS_M', '1500'))
    # Metro radius (20km) allows office desktops/laptops on Ethernet/LAN with city-level ISP geolocation (17.3934, 78.4706)
    OFFICE_METRO_RADIUS_M = int(os.getenv('OFFICE_METRO_RADIUS_M', '20000'))

    # Supported OTSi Office Locations for Geofencing
    OFFICE_LOCATIONS = [
        {"name": "OTSi Hyderabad HQ (Phoenix Infocity SEZ H02)", "lat": 17.4418, "lng": 78.3809, "radius": 1500},
        {"name": "OTSi Hyderabad (Campus 2 / HITEC City)", "lat": 17.4474, "lng": 78.3762, "radius": 1500},
    ]
    
    # Working hours
    WORKING_HOURS_PER_DAY = 8.5
    OFFICE_START_TIME = "09:00"
    OFFICE_END_TIME = "18:00"

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
