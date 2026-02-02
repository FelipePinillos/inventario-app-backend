# API de Ventas - Documentación

## Estructura de la Base de Datos

### Tabla `ventas`
```sql
- id (PK)
- id_cliente (FK a cliente)
- Fecha (datetime)
- TotalConDescuento (decimal)
- descuento (decimal)
- TotalSinDescuento (decimal)
- id_usuario (FK a usuario)
- estado (varchar, default 'CONFIRMADA')
```

### Tabla `detalle_venta`
```sql
- id (PK)
- id_venta (FK a ventas, cascade delete)
- id_presentacion (FK a presentaciones)
- cantidad (int)
- precio_unitario (decimal)
- subtotal (decimal)
```

**NOTA:** Se quitó `id_producto` porque ahora se accede al producto a través de la presentación.

## Endpoints Disponibles

### 1. Crear Venta
**POST** `/api/v1/ventas`

Crea una nueva venta con sus detalles. Automáticamente:
- Calcula totales basándose en los detalles
- Descuenta el stock según `cantidad_base` de cada presentación
- Valida stock disponible antes de crear

**Request Body:**
```json
{
  "id_cliente": 1,
  "Fecha": "2026-01-22T23:30:00",
  "descuento": 0,
  "id_usuario": 1,
  "estado": "CONFIRMADA",
  "detalles": [
    {
      "id_presentacion": 2,
      "cantidad": 2,
      "precio_unitario": 10.00,
      "subtotal": 20.00
    },
    {
      "id_presentacion": 11,
      "cantidad": 1,
      "precio_unitario": 200.00,
      "subtotal": 200.00
    },
    {
      "id_presentacion": 12,
      "cantidad": 1,
      "precio_unitario": 380.00,
      "subtotal": 380.00
    }
  ]
}
```

**Explicación del ejemplo:**
- Se venden **2 unidades individuales** del producto 4 (presentación id=2, unidad)
- Se vende **1 caja x25** del producto 4 (presentación id=11)
- Se vende **1 caja x50** del producto 4 (presentación id=12)

**Stock descontado:**
- `2 unidades × 1 (cantidad_base) = 2 unidades`
- `1 caja × 25 (cantidad_base) = 25 unidades`
- `1 caja × 50 (cantidad_base) = 50 unidades`
- **Total descontado del stock_actual: 77 unidades**

**Response:**
```json
{
  "id": 2,
  "id_cliente": 1,
  "Fecha": "2026-01-22T23:30:00",
  "descuento": 0.00,
  "TotalSinDescuento": 600.00,
  "TotalConDescuento": 600.00,
  "id_usuario": 1,
  "estado": "CONFIRMADA",
  "cliente": {
    "id": 1,
    "nombre": "Juan",
    "apellido": "Vergara",
    "dni": "77565228"
  },
  "usuario": {
    "id": 1,
    "nombre": "WUILSON FELIPE",
    "apellido": "PINILLOS VARAS"
  },
  "detalles": [
    {
      "id": 7,
      "id_venta": 2,
      "id_presentacion": 2,
      "cantidad": 2,
      "precio_unitario": 10.00,
      "subtotal": 20.00,
      "presentacion": {
        "id": 2,
        "nombre": "Unidad",
        "cantidad_base": 1,
        "precio": 10.00
      },
      "producto": {
        "id": 4,
        "codigo": "47523232",
        "nombre": "CUADERNO CUADRICULADO A-4"
      }
    },
    {
      "id": 8,
      "id_venta": 2,
      "id_presentacion": 11,
      "cantidad": 1,
      "precio_unitario": 200.00,
      "subtotal": 200.00,
      "presentacion": {
        "id": 11,
        "nombre": "Caja x 25",
        "cantidad_base": 25,
        "precio": 200.00
      },
      "producto": {
        "id": 4,
        "codigo": "47523232",
        "nombre": "CUADERNO CUADRICULADO A-4"
      }
    },
    {
      "id": 9,
      "id_venta": 2,
      "id_presentacion": 12,
      "cantidad": 1,
      "precio_unitario": 380.00,
      "subtotal": 380.00,
      "presentacion": {
        "id": 12,
        "nombre": "Caja x 50",
        "cantidad_base": 50,
        "precio": 380.00
      },
      "producto": {
        "id": 4,
        "codigo": "47523232",
        "nombre": "CUADERNO CUADRICULADO A-4"
      }
    }
  ]
}
```

### 2. Listar Ventas
**GET** `/api/v1/ventas?skip=0&limit=100`

Obtiene todas las ventas con sus detalles, paginadas.

### 3. Obtener Venta por ID
**GET** `/api/v1/ventas/{venta_id}`

Obtiene una venta específica con todos sus detalles.

### 4. Listar Ventas por Cliente
**GET** `/api/v1/ventas/cliente/{cliente_id}?skip=0&limit=100`

Obtiene todas las ventas de un cliente específico.

### 5. Listar Ventas por Usuario
**GET** `/api/v1/ventas/usuario/{usuario_id}?skip=0&limit=100`

Obtiene todas las ventas realizadas por un usuario (vendedor).

### 6. Listar Ventas por Rango de Fechas
**GET** `/api/v1/ventas/fecha/rango?fecha_inicio=2026-01-01T00:00:00&fecha_fin=2026-01-31T23:59:59`

Obtiene ventas dentro de un rango de fechas.

### 7. Actualizar Venta
**PUT** `/api/v1/ventas/{venta_id}`

Actualiza campos principales de la venta (NO actualiza detalles).
Solo administradores.

**Request Body:**
```json
{
  "estado": "CONFIRMADA",
  "descuento": 10.50
}
```

### 8. Cancelar Venta
**PATCH** `/api/v1/ventas/{venta_id}/cancelar`

Cancela una venta:
- Cambia estado a "CANCELADA"
- **Restaura el stock descontado**
- Solo administradores

### 9. Eliminar Venta
**DELETE** `/api/v1/ventas/{venta_id}`

⚠️ **ADVERTENCIA**: Elimina físicamente la venta.
- NO restaura el stock
- Los detalles se eliminan por cascade
- Solo administradores
- **Recomendación**: Usar cancelar_venta en su lugar

## Lógica de Stock

### Al Crear Venta:
```python
unidades_a_descontar = cantidad_vendida × presentacion.cantidad_base
producto.stock_actual -= unidades_a_descontar
```

**Ejemplo:**
- Vendo 3 cajas de "Caja x50" (presentación con cantidad_base=50)
- Se descuentan: `3 × 50 = 150 unidades` del stock_actual

### Al Cancelar Venta:
```python
unidades_a_restaurar = cantidad_vendida × presentacion.cantidad_base
producto.stock_actual += unidades_a_restaurar
```

## Validaciones

1. **Al crear venta:**
   - Debe tener al menos 1 detalle
   - Producto debe existir
   - Presentación debe existir
   - Stock suficiente para todas las presentaciones vendidas

2. **Stock insuficiente:**
   ```json
   {
     "detail": "Stock insuficiente para CUADERNO CUADRICULADO A-4. Disponible: 50, Requerido: 150"
   }
   ```

## Permisos

- **Crear venta**: Todos los usuarios autenticados
- **Listar/Ver ventas**: Todos los usuarios autenticados
- **Actualizar venta**: Solo administradores (id_tipo_usuario = 1)
- **Cancelar venta**: Solo administradores
- **Eliminar venta**: Solo administradores

## Notas Importantes

1. Los totales (`TotalSinDescuento` y `TotalConDescuento`) se calculan automáticamente
2. El stock se descuenta en **unidades base**, multiplicando por `cantidad_base`
3. Las presentaciones permiten vender el mismo producto en diferentes empaques
4. El campo `precio_unitario` en el detalle debe coincidir con el precio de la presentación
5. El `subtotal` debe ser: `cantidad × precio_unitario`
