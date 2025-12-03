"""
Configuration management for Outbound Omega v2
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///outbound_omega.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Anthropic AI
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')

    # Zoho Email
    ZOHO_SMTP_HOST = os.getenv('ZOHO_SMTP_HOST', 'smtp.zoho.com')
    ZOHO_SMTP_PORT = int(os.getenv('ZOHO_SMTP_PORT', '587'))
    ZOHO_USERNAME = os.getenv('ZOHO_USERNAME', '')
    ZOHO_PASSWORD = os.getenv('ZOHO_PASSWORD', '')

    # Sending Configuration
    MAX_EMAILS_PER_DAY_PER_ADDRESS = int(os.getenv('MAX_EMAILS_PER_DAY', '50'))

    # Compliance
    PHYSICAL_ADDRESS = os.getenv(
        'PHYSICAL_ADDRESS',
        '123 Business St, Suite 100, Atlanta, GA 30303'
    )
    UNSUBSCRIBE_BASE_URL = os.getenv(
        'UNSUBSCRIBE_BASE_URL',
        'http://localhost:5000/unsubscribe'
    )
    COMPANY_NAME = os.getenv('COMPANY_NAME', 'Your Company Name')

    # From Addresses (comma-separated)
    FROM_ADDRESSES = os.getenv(
        'FROM_ADDRESSES',
        'outreach@yourcompany.com,hello@yourcompany.com'
    ).split(',')

    # Scraper Integration
    SCRAPER_ENDPOINT = os.getenv('SCRAPER_ENDPOINT', 'http://localhost:5000/scrape')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
