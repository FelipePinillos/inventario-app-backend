from app.database import engine, Base
from app.models import *

# Esta función crea las tablas en la base de datos
def crear_tablas():
    try:
        Base.metadata.create_all(bind=engine)
        print("Tablas creadas correctamente")
    except Exception as e:
        print(f"Error al crear tablas: {e}")

if __name__ == "__main__":
    crear_tablas()


