"""
Script de migración para agregar el campo precio_compra a la tabla detalle_compra
(almacena el precio de compra al momento de la transacción para histórico)
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
        
        # Verificar si la columna ya existe
        print("🔍 Verificando si la columna precio_compra ya existe...")
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'detalle_compra' 
            AND column_name = 'precio_compra'
        """))
        
        if result.fetchone():
            print("⚠️  La columna precio_compra ya existe en detalle_compra")
        else:
            print("➕ Agregando columna precio_compra a detalle_compra...")
            
            # Agregar la columna precio_compra (permitir NULL temporalmente)
            conn.execute(text("""
                ALTER TABLE detalle_compra 
                ADD COLUMN precio_compra NUMERIC(10, 2)
            """))
            conn.commit()
            print("✅ Columna precio_compra agregada")
            
            # Actualizar los registros existentes con el precio_compra de la presentación
            print("🔄 Actualizando registros existentes con precio_compra de presentación...")
            conn.execute(text("""
                UPDATE detalle_compra dc
                SET precio_compra = p.precio_compra
                FROM presentaciones p
                WHERE dc.id_presentacion = p.id
            """))
            conn.commit()
            print("✅ Registros actualizados")
            
            # Hacer la columna NOT NULL
            print("🔒 Configurando columna precio_compra como NOT NULL...")
            conn.execute(text("""
                ALTER TABLE detalle_compra 
                ALTER COLUMN precio_compra SET NOT NULL
            """))
            conn.commit()
            print("✅ Columna configurada como NOT NULL")
        
        print("\n✨ Migración completada exitosamente")
        
except Exception as e:
    print(f"❌ Error durante la migración: {str(e)}")
    sys.exit(1)
