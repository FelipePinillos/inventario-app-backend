"""
Script de migración para actualizar las compras
- Cambiar nombres de columnas en tabla compras
- Agregar campos de fecha_creacion y fecha_edicion
- Crear tabla detalle_compra
- Quitar referencias a estado_pago
"""

import os
import sys

# Agregar el directorio raíz al path para las importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlalchemy import text

def ejecutar_migracion():
    print("Iniciando migración de compras...")
    
    with engine.connect() as connection:
        try:
            # Verificar si existe la tabla compras
            result = connection.execute(text("SHOW TABLES LIKE 'compras'"))
            if not result.fetchone():
                print("Tabla compras no existe. Crear las tablas primero.")
                return
            
            # 1. Agregar nuevas columnas si no existen
            print("1. Verificando y agregando columnas faltantes...")
            
            try:
                connection.execute(text("ALTER TABLE compras ADD COLUMN fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"))
                print("   - Agregada columna fecha_creacion")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("   - Columna fecha_creacion ya existe")
                else:
                    print(f"   - Error agregando fecha_creacion: {e}")
            
            try:
                connection.execute(text("ALTER TABLE compras ADD COLUMN fecha_edicion DATETIME NULL"))
                print("   - Agregada columna fecha_edicion")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("   - Columna fecha_edicion ya existe")
                else:
                    print(f"   - Error agregando fecha_edicion: {e}")
            
            # 2. Cambiar nombres de columnas si es necesario
            print("2. Verificando nombres de columnas...")
            
            # Verificar si existe TotalConDescuento
            try:
                connection.execute(text("ALTER TABLE compras CHANGE TotalConDescuento totalcondescuento DECIMAL(10,2)"))
                print("   - Renombrada TotalConDescuento a totalcondescuento")
            except Exception as e:
                if "Unknown column" in str(e):
                    print("   - Columna TotalConDescuento no existe o ya fue renombrada")
                else:
                    print(f"   - Error renombrando TotalConDescuento: {e}")
            
            try:
                connection.execute(text("ALTER TABLE compras CHANGE TotalSinDescuento totalsindescuento DECIMAL(10,2) NOT NULL"))
                print("   - Renombrada TotalSinDescuento a totalsindescuento")
            except Exception as e:
                if "Unknown column" in str(e):
                    print("   - Columna TotalSinDescuento no existe o ya fue renombrada")
                else:
                    print(f"   - Error renombrando TotalSinDescuento: {e}")
            
            # 3. Quitar columna id_estado si existe
            print("3. Verificando columna id_estado...")
            try:
                connection.execute(text("ALTER TABLE compras DROP COLUMN id_estado"))
                print("   - Eliminada columna id_estado")
            except Exception as e:
                if "check that column" in str(e):
                    print("   - Columna id_estado no existe")
                else:
                    print(f"   - Error eliminando id_estado: {e}")
            
            # 4. Crear tabla detalle_compra
            print("4. Creando tabla detalle_compra...")
            create_detalle_compra_sql = """
                CREATE TABLE IF NOT EXISTS detalle_compra (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_compra INT NOT NULL,
                    id_presentacion INT NOT NULL,
                    cantidad INT NOT NULL,
                    subtotal DECIMAL(10,2) NOT NULL,
                    precio_compra DECIMAL(10,2) NOT NULL,
                    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    fecha_edicion DATETIME NULL,
                    FOREIGN KEY (id_compra) REFERENCES compras(id) ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY (id_presentacion) REFERENCES presentaciones(id) ON DELETE CASCADE ON UPDATE CASCADE
                )
            """
            connection.execute(text(create_detalle_compra_sql))
            print("   - Tabla detalle_compra creada exitosamente")
            
            # 5. Commit de todos los cambios
            connection.commit()
            print("\nMigración completada exitosamente!")
            
        except Exception as e:
            print(f"Error durante la migración: {e}")
            connection.rollback()

if __name__ == "__main__":
    ejecutar_migracion()