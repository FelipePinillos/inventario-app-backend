from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from app.models.producto import Producto
from app.schemas.producto import ProductoCreate, ProductoUpdate


def crear_producto_db(db: Session, producto: ProductoCreate) -> Producto:
    """Crea un nuevo producto."""
    # Verificar si ya existe un producto ACTIVO con el mismo código
    producto_existente = db.query(Producto).filter(
        Producto.codigo == producto.codigo,
        Producto.estado == 'A'
    ).first()
    
    if producto_existente:
        raise ValueError("Ya existe un producto activo con ese código")
    
    fecha_actual = datetime.now().isoformat()
    db_producto = Producto(
        codigo=producto.codigo,
        nombre=producto.nombre,
        adicional=producto.adicional,
        stock_minimo=producto.stock_minimo,
        stock_actual=producto.stock_actual,
        stock_maximo=producto.stock_maximo,
        avatar=producto.avatar,
        id_categoria=producto.id_categoria,
        id_tipo_producto=producto.id_tipo_producto,
        id_marca=producto.id_marca,
        estado='A',
        fecha_creacion=fecha_actual,
        fecha_edicion=fecha_actual
    )
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto


def obtener_productos_db(db: Session, incluir_inactivos: bool = False) -> list[Producto]:
    """Obtiene todos los productos. Por defecto solo los activos."""
    query = db.query(Producto).options(
        joinedload(Producto.categoria),
        joinedload(Producto.marca),
        joinedload(Producto.tipo_producto),
        joinedload(Producto.presentaciones)
    )
    
    if not incluir_inactivos:
        query = query.filter(Producto.estado == 'A')
    
    return query.order_by(Producto.id.desc()).all()


def obtener_producto_db(db: Session, producto_id: int) -> Producto | None:
    """Obtiene un producto por ID."""
    return db.query(Producto).options(
        joinedload(Producto.categoria),
        joinedload(Producto.marca),
        joinedload(Producto.tipo_producto),
        joinedload(Producto.presentaciones)
    ).filter(
        Producto.id == producto_id,
        Producto.estado == 'A'
    ).first()


def obtener_producto_por_codigo_db(db: Session, codigo: str) -> Producto | None:
    """Obtiene un producto por código."""
    return db.query(Producto).filter(
        Producto.codigo == codigo,
        Producto.estado == 'A'
    ).first()


def actualizar_producto_db(db: Session, producto_id: int, producto_update: ProductoUpdate) -> Producto:
    """Actualiza un producto."""
    db_producto = obtener_producto_db(db, producto_id)
    
    if not db_producto:
        raise ValueError("Producto no encontrado")
    
    # Actualizar solo los campos que se enviaron
    if producto_update.codigo is not None:
        # Verificar que no exista otro producto con el mismo código
        producto_existente = db.query(Producto).filter(
            Producto.codigo == producto_update.codigo,
            Producto.id != producto_id
        ).first()
        
        if producto_existente:
            raise ValueError("Ya existe otro producto con ese código")
        
        db_producto.codigo = producto_update.codigo
    
    if producto_update.nombre is not None:
        db_producto.nombre = producto_update.nombre
    if producto_update.adicional is not None:
        db_producto.adicional = producto_update.adicional
    if producto_update.stock_minimo is not None:
        db_producto.stock_minimo = producto_update.stock_minimo
    if producto_update.stock_actual is not None:
        db_producto.stock_actual = producto_update.stock_actual
    if producto_update.stock_maximo is not None:
        db_producto.stock_maximo = producto_update.stock_maximo
    if producto_update.avatar is not None:
        db_producto.avatar = producto_update.avatar
    if producto_update.id_categoria is not None:
        db_producto.id_categoria = producto_update.id_categoria
    if producto_update.id_tipo_producto is not None:
        db_producto.id_tipo_producto = producto_update.id_tipo_producto
    if producto_update.id_marca is not None:
        db_producto.id_marca = producto_update.id_marca
    
    db_producto.fecha_edicion = datetime.now().isoformat()
    db.commit()
    db.refresh(db_producto)
    return db_producto


def eliminar_producto_db(db: Session, producto_id: int) -> bool:
    """Elimina un producto (eliminación lógica)."""
    db_producto = obtener_producto_db(db, producto_id)
    
    if not db_producto:
        raise ValueError("Producto no encontrado")
    
    # Eliminación lógica: cambiar estado a 'I' (Inactivo)
    db_producto.estado = 'I'
    db_producto.fecha_edicion = datetime.now().isoformat()
    db.commit()
    return True

