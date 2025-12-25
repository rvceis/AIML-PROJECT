import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = False
    TESTING = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'textile_generator')
    DB_USER = os.getenv('DB_USER', 'textile_user')
    DB_PASS = os.getenv('DB_PASS', 'textile_pass')
    
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Paths
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MODEL_PATH = os.getenv('MODEL_PATH', '../models')
    
    # Generation defaults
    DEFAULT_STEPS = 30
    DEFAULT_GUIDANCE = 7.5
    IMAGE_SIZE = 512  # Reduced to 512 for 4GB GPUs (was 1024)
    IMAGE_FORMAT = 'PNG'
    
    # SDXL Model settings
    SDXL_MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
    LORA_ADAPTER_PATH = os.path.join(MODEL_PATH, "adapter_config.json")
    
    # Supported styles
    SUPPORTED_STYLES = [
        {"id": "bandhani", "name": "Bandhani", "description": "Traditional tie-dye patterns"},
        {"id": "ikat", "name": "Ikat", "description": "Resist-dyed textile patterns"},
        {"id": "block_print", "name": "Block Print", "description": "Hand-stamped patterns"},
        {"id": "paisley", "name": "Paisley", "description": "Classic paisley motifs"},
    ]


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Use SQLite for easy development (no PostgreSQL setup needed)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///textile_generator.db'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Strong secrets should be supplied via environment in real deployments
    SECRET_KEY = os.getenv('SECRET_KEY', 'replace-with-strong-secret')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'replace-with-strong-jwt-secret')
    REQUIRE_STRONG_SECRETS = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=5)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
