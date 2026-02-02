"""
Migración para quitar id_producto de detalle_venta
Fecha: 2024-02-02

IMPORTANTE: Esta migración quita la columna id_producto de la tabla detalle_venta
porque ahora se accede al producto a través de la presentación.

ANTES de ejecutar esta migración:
1. Hacer un backup de la base de datos
2. Verificar que no hay datos importantes que se puedan perder
3. Asegurarse de que la aplicación esté actualizada con los nuevos modelos

SQL para ejecutar:
"""

# Migración SQL para quitar id_producto de detalle_venta
migration_sql = """
-- Paso 1: Quitar la restricción de clave foránea
ALTER TABLE detalle_venta DROP CONSTRAINT IF EXISTS detalle_venta_id_producto_fkey;

-- Paso 2: Quitar la columna id_producto
ALTER TABLE detalle_venta DROP COLUMN IF EXISTS id_producto;

-- Verificación: Describir la tabla después del cambio
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'detalle_venta' 
ORDER BY ordinal_position;
"""

if __name__ == "__main__":
    print("MIGRACIÓN: Quitar id_producto de detalle_venta")
    print("=" * 50)
    print(migration_sql)
    print("\nEJECUTAR MANUALMENTE EN LA BASE DE DATOS")
    print("NO ejecutar este script directamente")