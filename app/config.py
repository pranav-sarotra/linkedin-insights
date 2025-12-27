import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings for the application"""
    
    # database settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'linkedin_insights')
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # app settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key_change_in_production')
    
    # cache settings
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # openai for bonus feature
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # pagination defaults
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 50