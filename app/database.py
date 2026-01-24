from sqlalchemy import create_engine # Motor de base de datos
from sqlalchemy.ext.declarative import declarative_base # Base para los modelos
from sqlalchemy.orm import sessionmaker # Crear sesiones
from app.config import get_settings


#Ahora vamos a crear los modelos y las migraciones

from fastapi import Depends # Dependencias, para inyectar la sesión de base de datos

# Obtener la configuración desde variables de entorno
settings = get_settings()

engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# esta función crea una nueva sesión de base de datos para cada solicitud
def get_db():
    db = SessionLocal()
    try:
        yield db # yield es como return pero para generadores
    finally:
        db.close() # Cierra la sesión de la base de datos