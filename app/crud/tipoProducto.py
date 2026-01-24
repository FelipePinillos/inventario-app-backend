from sqlalchemy.orm import Session
from datetime import datetime
from app.models.tipoProducto import TipoProducto
from app.schemas.tipoProducto import TipoProductoCreate, TipoProductoUpdate


def crear_tipo_producto_db(db: Session, tipo_producto: TipoProductoCreate) -> TipoProducto:
    """Crea un nuevo tipo de producto."""
    # Verificar si ya existe un tipo de producto ACTIVO con el mismo nombre
    tipo_existente = db.query(TipoProducto).filter(
        TipoProducto.nombre == tipo_producto.nombre,
        TipoProducto.estado == 'A'
    ).first()
    
    if tipo_existente:
        raise ValueError("Ya existe un tipo de producto activo con ese nombre")
    
    db_tipo_producto = TipoProducto(
        nombre=tipo_producto.nombre,
        estado='A'
    )
    db.add(db_tipo_producto)
    db.commit()
    db.refresh(db_tipo_producto)
    return db_tipo_producto


def obtener_tipos_producto_db(db: Session, incluir_inactivas: bool = False) -> list[TipoProducto]:
    """Obtiene todos los tipos de producto. Por defecto solo los activos."""
    query = db.query(TipoProducto)
    
    if not incluir_inactivas:
        query = query.filter(TipoProducto.estado == 'A')
    
    return query.order_by(TipoProducto.id.desc()).all()


def obtener_tipo_producto_db(db: Session, tipo_producto_id: int) -> TipoProducto | None:
    """Obtiene un tipo de producto por ID."""
    return db.query(TipoProducto).filter(
        TipoProducto.id == tipo_producto_id,
        TipoProducto.estado == 'A'
    ).first()


def actualizar_tipo_producto_db(db: Session, tipo_producto_id: int, tipo_producto_update: TipoProductoUpdate) -> TipoProducto:
    """Actualiza un tipo de producto."""
    db_tipo_producto = obtener_tipo_producto_db(db, tipo_producto_id)
    
    if not db_tipo_producto:
        raise ValueError("Tipo de producto no encontrado")
    
    # Actualizar solo los campos que se enviaron
    if tipo_producto_update.nombre is not None:
        # Verificar que no exista otro tipo de producto con el mismo nombre
        tipo_existente = db.query(TipoProducto).filter(
            TipoProducto.nombre == tipo_producto_update.nombre,
            TipoProducto.id != tipo_producto_id
        ).first()
        
        if tipo_existente:
            raise ValueError("Ya existe otro tipo de producto con ese nombre")
        
        db_tipo_producto.nombre = tipo_producto_update.nombre
    
    db_tipo_producto.fecha_edicion = datetime.now()
    db.commit()
    db.refresh(db_tipo_producto)
    return db_tipo_producto


def eliminar_tipo_producto_db(db: Session, tipo_producto_id: int) -> bool:
    """Elimina un tipo de producto (eliminación lógica)."""
    db_tipo_producto = obtener_tipo_producto_db(db, tipo_producto_id)
    
    if not db_tipo_producto:
        raise ValueError("Tipo de producto no encontrado")
    
    # No permitir eliminar el tipo "NO ASIGNADO" (id=1)
    if db_tipo_producto.id == 1:
        raise ValueError("No se puede eliminar el tipo 'NO ASIGNADO'")
    
    # Eliminación lógica: cambiar estado a 'I' (Inactivo)
    db_tipo_producto.estado = 'I'
    db_tipo_producto.fecha_edicion = datetime.now()
    db.commit()
    return True
