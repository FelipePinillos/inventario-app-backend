# Resumen del Cambio: precio → precio_venta

## Cambios Realizados

### 1. Modelo de Base de Datos
**Archivo: `app/models/presentacion.py`**
```python
# ANTES:
precio = Column(Float, nullable=False)  # Precio de esta presentación

# DESPUÉS:
precio_venta = Column(Float, nullable=False)  # Precio de venta de esta presentación
```

### 2. Schemas de Presentación
**Archivo: `app/schemas/presentacion.py`**
```python
# ANTES:
class PresentacionBase(BaseModel):
    id_producto: int
    nombre: str
    cantidad_base: int
    precio: float  # ❌ Campo anterior

class PresentacionUpdate(BaseModel):
    precio: Optional[float] = None  # ❌ Campo anterior

# DESPUÉS:
class PresentacionBase(BaseModel):
    id_producto: int
    nombre: str
    cantidad_base: int
    precio_venta: float  # ✅ Nuevo campo

class PresentacionUpdate(BaseModel):
    precio_venta: Optional[float] = None  # ✅ Nuevo campo
```

### 3. Schemas de Venta
**Archivo: `app/schemas/venta.py`**
```python
# ANTES:
class PresentacionSimple(BaseModel):
    precio: Decimal  # ❌ Campo anterior

# DESPUÉS:
class PresentacionSimple(BaseModel):
    precio_venta: Decimal  # ✅ Nuevo campo
```

### 4. Schemas de Producto
**Archivo: `app/schemas/producto.py`**
```python
# ANTES:
"precio": presentacion.precio  # ❌ Campo anterior

# DESPUÉS:
"precio_venta": presentacion.precio_venta  # ✅ Nuevo campo
```

## Estructura Final de la Tabla Presentaciones

```sql
CREATE TABLE presentaciones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_producto INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    cantidad_base INT NOT NULL,
    precio_venta FLOAT NOT NULL,  -- ✅ CAMPO RENOMBRADO
    estado VARCHAR(10) DEFAULT 'A',
    fecha_creacion VARCHAR(25) NOT NULL,
    fecha_edicion VARCHAR(25),
    FOREIGN KEY (id_producto) REFERENCES producto(id) ON DELETE CASCADE
);
```

## API Endpoints Afectados

### POST /api/v1/presentaciones
```json
{
    "id_producto": 1,
    "nombre": "Unidad",
    "cantidad_base": 1,
    "precio_venta": 25.50  // ✅ Campo renombrado
}
```

### PUT /api/v1/presentaciones/{id}
```json
{
    "nombre": "Caja x12",
    "cantidad_base": 12,
    "precio_venta": 280.00  // ✅ Campo renombrado
}
```

### Respuestas de GET
```json
{
    "id": 1,
    "id_producto": 1,
    "nombre": "Unidad",
    "cantidad_base": 1,
    "precio_venta": 25.50,  // ✅ Campo renombrado
    "producto": {
        "codigo": "PROD001",
        "nombre": "Producto Ejemplo"
    }
}
```

## Migración de Base de Datos

Para aplicar estos cambios a tu base de datos existente, ejecuta:

```bash
python migration_precio_venta.py
```

Este script:
1. Verificará si la columna `precio` existe
2. La renombrará a `precio_venta`
3. Confirmará que la migración fue exitosa

## Archivos que NO requieren cambios

- ✅ `app/crud/presentacion.py` - Usa `model_dump()` automáticamente
- ✅ `app/routers/presentaciones.py` - Usa los schemas actualizados
- ✅ Cualquier otro CRUD/Router que use los schemas

## Próximos pasos

1. **Ejecutar migración**: `python migration_precio_venta.py`
2. **Reiniciar servidor**: Para cargar los nuevos modelos
3. **Probar endpoints**: Verificar que todo funciona correctamente
4. **Actualizar frontend**: Si tienes una aplicación frontend, actualizar las referencias al campo

## Beneficios del cambio

- ✅ **Más descriptivo**: `precio_venta` es más claro que solo `precio`
- ✅ **Preparado para expansión**: Facilita agregar otros tipos de precio (compra, mayorista, etc.)
- ✅ **Consistencia**: Mejor nomenclatura en la base de datos