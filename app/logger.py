"""
Configuración de logging para la aplicación.
"""
import logging
import os
from pathlib import Path

# Crear directorio de logs si no existe
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configurar logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
