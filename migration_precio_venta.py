"""
Script de migración para cambiar el nombre de la columna 'precio' a 'precio_venta' 
en la tabla 'presentaciones'.

Ejecutar este script después de actualizar los modelos para sincronizar la base de datos.
"""

import os
import sys
from sqlalchemy import text, inspect

# Agregar el directorio raíz al PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, get_db

def migrate_precio_to_precio_venta():
    """
    Migra la columna 'precio' a 'precio_venta' en la tabla presentaciones.
    """
    print("Iniciando migración: precio -> precio_venta")
    
    try:
        with engine.connect() as connection:
            # Verificar si existe la columna 'precio'
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('presentaciones')]
            
            if 'precio' in columns and 'precio_venta' not in columns:
                print("Ejecutando migración: Renombrando columna 'precio' a 'precio_venta'")
                
                # Renombrar la columna (esto puede variar según el motor de base de datos)
                # Para MySQL/MariaDB:
                connection.execute(text("""
                    ALTER TABLE presentaciones 
                    CHANGE COLUMN precio precio_venta FLOAT NOT NULL
                """))
                
                # Para PostgreSQL usarías:
                # connection.execute(text("""
                #     ALTER TABLE presentaciones 
                #     RENAME COLUMN precio TO precio_venta
                # """))
                
                # Para SQLite (más complejo, requiere recrear la tabla)
                # No recomendado para producción
                
                connection.commit()
                print("✅ Migración completada exitosamente")
                
            elif 'precio_venta' in columns:
                print("⚠️  La columna 'precio_venta' ya existe. Migración no necesaria.")
                
            elif 'precio' not in columns:
                print("⚠️  La columna 'precio' no existe. Posiblemente ya migrada.")
                
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        print("Asegúrate de hacer un backup de la base de datos antes de ejecutar migraciones.")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Script de migración: precio -> precio_venta")
    print("=" * 50)
    
    # Verificar conexión a la base de datos
    try:
        with engine.connect() as connection:
            print("✅ Conexión a la base de datos establecida")
    except Exception as e:
        print(f"❌ No se pudo conectar a la base de datos: {e}")
        sys.exit(1)
    
    # Ejecutar migración
    resultado = migrate_precio_to_precio_venta()
    
    if resultado:
        print("\n🎉 Proceso completado")
        print("Recuerda reiniciar tu servidor FastAPI para aplicar los cambios en los modelos.")
    else:
        print("\n⚠️  Migración no completada")
        print("Revisa los errores anteriores y vuelve a intentar.")