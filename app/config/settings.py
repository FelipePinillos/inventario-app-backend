"""
Configuración centralizada de la aplicación.
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # Base de datos
    # Para MySQL:
    # "mysql+pymysql://usuario:contraseña@localhost:3306/nombrebasedatos"
    # Para PostgreSQL:
    # "postgresql+psycopg2://usuario:contraseña@localhost:5432/nombrebasedatos"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        # Ejemplo para MySQL:
        #"mysql+pymysql://root@localhost:3306/sistemalibreria"
        # Ejemplo para PostgreSQL:
        "postgresql+psycopg2://postgres:Inge2020@localhost:5432/sistemalibreria"

    )
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tu-clave-secreta-muy-segura-cambiar-en-produccion")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API
    API_TITLE: str = "API Inventario y Ventas"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API para gestión de inventario, ventas y predicción"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Obtiene la instancia de configuración."""
    return Settings()
