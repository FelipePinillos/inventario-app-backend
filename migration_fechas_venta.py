"""
Migración para agregar fecha_creacion y fecha_edicion a la tabla ventas
"""

from sqlalchemy import text
from app.database import engine

def agregar_fechas_venta():
    """Agregar columnas fecha_creacion y fecha_edicion a la tabla ventas"""
    
    try:
        with engine.begin() as connection:
            # Verificar si las columnas ya existen
            result = connection.execute(text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'ventas' 
                AND COLUMN_NAME IN ('fecha_creacion', 'fecha_edicion')
            """))
            
            existing_columns = result.fetchone()[0]
            
            if existing_columns < 2:
                print("Agregando columnas fecha_creacion y fecha_edicion a tabla ventas...")
                
                # Agregar fecha_creacion (NOT NULL con valor por defecto)
                connection.execute(text("""
                    ALTER TABLE ventas 
                    ADD COLUMN fecha_creacion VARCHAR(25) 
                    DEFAULT '' NOT NULL
                """))
                
                # Agregar fecha_edicion (NULL)
                connection.execute(text("""
                    ALTER TABLE ventas 
                    ADD COLUMN fecha_edicion VARCHAR(25) 
                    NULL
                """))
                
                # Actualizar registros existentes con fecha actual
                connection.execute(text("""
                    UPDATE ventas 
                    SET fecha_creacion = DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')
                    WHERE fecha_creacion = ''
                """))
                
                print("✅ Columnas agregadas exitosamente")
            else:
                print("ℹ️  Las columnas ya existen")
                
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        raise e

if __name__ == "__main__":
    print("🔄 Iniciando migración de fechas para ventas...")
    agregar_fechas_venta()
    print("✅ Migración completada")