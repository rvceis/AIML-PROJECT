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
    MODEL_PATH = os.getenv('MODEL_PATH', '../textile_loras_trained')
    
    # Generation defaults
    DEFAULT_STEPS = 15  # Reduced for faster generation
    DEFAULT_GUIDANCE = 7.5
    IMAGE_SIZE = 512  
    IMAGE_FORMAT = 'PNG'
    
    # Performance optimization settings for faster inference
    ENABLE_XFORMERS = True  # Enable xFormers for 40% faster attention
    ENABLE_VAE_TILING = True  # Enable VAE tiling to reduce memory pressure
    ENABLE_ATTENTION_SLICING = False  # Fallback if xformers unavailable
    SCHEDULER = 'DPM++'  # Faster scheduler: 'DPM++', 'Euler', 'LMSDiscrete'
    
    # LoRA Model settings (Stable Diffusion v1.5 based)
    BASE_MODEL_ID = "runwayml/stable-diffusion-v1-5"
    LORA_BASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'textile_loras_trained')
    
    # Supported styles and patterns
    SUPPORTED_STYLES = [
        {
            "id": "bandhani", 
            "name": "Bandhani", 
            "description": "Traditional tie-dye patterns",
            "patterns": [
                {"id": "leheriya", "name": "Leheriya", "description": "Diagonal wave resist"},
                {"id": "mothra", "name": "Mothra", "description": "Small dot grid"},
                {"id": "ekdali", "name": "Ekdali", "description": "Single dot clusters"},
                {"id": "shikari", "name": "Shikari", "description": "Dense dotted fields"},
                {"id": "gharchola", "name": "Gharchola", "description": "Checkered bandhani grid"},
            ]
        },
        {
            "id": "batik", 
            "name": "Batik", 
            "description": "Wax-resist dyeing technique",
            "patterns": [
                {"id": "parang", "name": "Parang", "description": "Diagonal knife motifs"},
                {"id": "kawung", "name": "Kawung", "description": "Oval palm-fruit shapes"},
                {"id": "mega_mendung", "name": "Mega Mendung", "description": "Layered cloud forms"},
                {"id": "truntum", "name": "Truntum", "description": "Star-flower repeats"},
                {"id": "ceplok", "name": "Ceplok", "description": "Geometric medallions"},
            ]
        },
        {
            "id": "ikat", 
            "name": "Ikat", 
            "description": "Resist-dyed textile patterns",
            "patterns": [
                {"id": "patola", "name": "Patola", "description": "Double-ikat geometrics"},
                {"id": "pochampally", "name": "Pochampally", "description": "Rhombus checks"},
                {"id": "telia_rumal", "name": "Telia Rumal", "description": "Oil-resist stripes"},
                {"id": "sambalpuri", "name": "Sambalpuri", "description": "Traditional ikat motifs"},
                {"id": "geringsing", "name": "Geringsing", "description": "Balinese double-ikat"},
            ]
        },
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
