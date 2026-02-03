"""
Script para sincronizar las secuencias de autoincremento con los datos existentes
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

# Tablas con secuencias a sincronizar
tables = [
    'compras',
    'detalle_compra',
    'ventas',
    'detalle_venta',
    'producto',
    'presentaciones',
    'categoria',
    'marca',
    'tipo_producto',
    'proveedor',
    'cliente',
    'usuario'
]

try:
    with engine.connect() as conn:
        print("✅ Conexión exitosa\n")
        
        for table in tables:
            print(f"🔍 Procesando tabla: {table}")
            
            # Obtener el máximo ID actual
            result = conn.execute(text(f"SELECT MAX(id) FROM {table}"))
            max_id = result.scalar()
            
            if max_id is None:
                print(f"   ⚠️  Tabla {table} está vacía, omitiendo...")
                continue
            
            # Sincronizar la secuencia
            sequence_name = f"{table}_id_seq"
            try:
                conn.execute(text(f"SELECT setval('{sequence_name}', :max_id, true)"), {"max_id": max_id})
                conn.commit()
                print(f"   ✅ Secuencia {sequence_name} sincronizada con max_id={max_id}")
            except Exception as e:
                print(f"   ⚠️  No se pudo sincronizar {sequence_name}: {str(e)}")
        
        print("\n✨ Sincronización completada")
        
except Exception as e:
    print(f"❌ Error durante la sincronización: {str(e)}")
    sys.exit(1)
