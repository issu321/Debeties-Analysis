"""
Debeties Analysis V2 - Configuration
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'debeties-flask-v2-super-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or         'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'debeties.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Paths
    DATA_PATH = os.path.join(BASE_DIR, 'data', 'diabetes.csv')
    MODELS_DIR = os.path.join(BASE_DIR, 'models')

    # App settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload

    # Branding
    BRAND_NAME = "Debeties Analysis"
    BRAND_TAGLINE = "AI-Powered Diabetes Risk Assessment"
    BRAND_AUTHOR = "Mohammed Usman"
    BRAND_GITHUB = "https://github.com/issu321/Debeties-Analysis"
    BRAND_PORTFOLIO = "https://issu321.github.io/issu321"
