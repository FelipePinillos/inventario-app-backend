"""
Script de migración para renombrar precio_unitario a precio_compra en detalle_compra
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
        
        # Verificar si la columna precio_unitario existe
        print("🔍 Verificando columna precio_unitario...")
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'detalle_compra' 
            AND column_name = 'precio_unitario'
        """))
        
        if result.fetchone():
            print("✏️  Renombrando columna precio_unitario a precio_compra...")
            conn.execute(text("""
                ALTER TABLE detalle_compra 
                RENAME COLUMN precio_unitario TO precio_compra
            """))
            conn.commit()
            print("✅ Columna renombrada exitosamente")
        else:
            # Verificar si ya existe como precio_compra
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'detalle_compra' 
                AND column_name = 'precio_compra'
            """))
            
            if result.fetchone():
                print("⚠️  La columna ya se llama precio_compra")
            else:
                print("❌ No se encontró la columna precio_unitario ni precio_compra")
                sys.exit(1)
        
        print("\n✨ Migración completada exitosamente")
        
except Exception as e:
    print(f"❌ Error durante la migración: {str(e)}")
    sys.exit(1)
