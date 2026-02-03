"""
Script para corregir la restricción de clave foránea en detalle_compra
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener URL de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: No se encontró DATABASE_URL en las variables de entorno")
    sys.exit(1)

print(f"🔗 Conectando a la base de datos...")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("✅ Conexión exitosa")
        
        # Eliminar la restricción incorrecta si existe
        print("🔍 Verificando restricción fk_detalle_compra_producto...")
        result = conn.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'detalle_compra' 
            AND constraint_name = 'fk_detalle_compra_producto'
        """))
        
        if result.fetchone():
            print("🗑️  Eliminando restricción incorrecta fk_detalle_compra_producto...")
            conn.execute(text("""
                ALTER TABLE detalle_compra 
                DROP CONSTRAINT IF EXISTS fk_detalle_compra_producto
            """))
            conn.commit()
            print("✅ Restricción eliminada")
        else:
            print("⚠️  Restricción fk_detalle_compra_producto no existe")
        
        # Verificar si ya existe la restricción correcta
        print("🔍 Verificando restricción correcta...")
        result = conn.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'detalle_compra' 
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name LIKE '%presentacion%'
        """))
        
        if result.fetchone():
            print("✅ Ya existe una restricción correcta hacia presentaciones")
        else:
            # Crear la restricción correcta
            print("➕ Creando restricción correcta hacia presentaciones...")
            conn.execute(text("""
                ALTER TABLE detalle_compra 
                ADD CONSTRAINT detalle_compra_id_presentacion_fkey 
                FOREIGN KEY (id_presentacion) 
                REFERENCES presentaciones(id) 
                ON DELETE CASCADE 
                ON UPDATE CASCADE
            """))
            conn.commit()
            print("✅ Restricción creada exitosamente")
        
        print("\n✨ Corrección completada exitosamente")
        
except Exception as e:
    print(f"❌ Error durante la corrección: {str(e)}")
    sys.exit(1)
