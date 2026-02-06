from sqlalchemy.orm import Session, joinedload
from app.models.compra import Compra, DetalleCompra
from app.models.presentacion import Presentacion
from app.models.producto import Producto
from app.schemas.compra import CompraCreate, CompraUpdate, DetalleCompraCreate, DetalleCompraUpdate
from typing import Optional, List
from datetime import date
import datetime

def get_compras(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[Compra]:
    """Obtener lista de compras con relaciones, ordenadas por ID descendente"""
    return db.query(Compra)\
        .options(
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor),
            joinedload(Compra.detalles).joinedload(DetalleCompra.presentacion).joinedload(Presentacion.producto)
        )\
        .order_by(Compra.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_compra_by_id(db: Session, compra_id: int) -> Optional[Compra]:
    """Obtener una compra por ID con sus relaciones"""
    return db.query(Compra)\
        .options(
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor),
            joinedload(Compra.detalles).joinedload(DetalleCompra.presentacion).joinedload(Presentacion.producto)
        )\
        .filter(Compra.id == compra_id)\
        .first()

def get_compras_by_proveedor(
    db: Session, 
    proveedor_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Compra]:
    """Obtener compras por proveedor"""
    return db.query(Compra)\
        .options(
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor),
            joinedload(Compra.detalles).joinedload(DetalleCompra.presentacion).joinedload(Presentacion.producto)
        )\
        .filter(Compra.id_proveedor == proveedor_id)\
        .order_by(Compra.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_compras_by_usuario(
    db: Session, 
    usuario_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Compra]:
    """Obtener compras por usuario"""
    return db.query(Compra)\
        .options(
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor),
            joinedload(Compra.detalles).joinedload(DetalleCompra.presentacion).joinedload(Presentacion.producto)
        )\
        .filter(Compra.id_usuario == usuario_id)\
        .order_by(Compra.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def get_compras_by_fecha(
    db: Session,
    fecha_inicio: date,
    fecha_fin: date,
    skip: int = 0,
    limit: int = 100
) -> List[Compra]:
    """Obtener compras por rango de fecha de compra (fecha_compra)."""
    return db.query(Compra)\
        .options(
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor),
            joinedload(Compra.detalles).joinedload(DetalleCompra.presentacion).joinedload(Presentacion.producto)
        )\
        .filter(Compra.fecha_compra >= fecha_inicio, Compra.fecha_compra <= fecha_fin)\
        .order_by(Compra.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def crear_compra(db: Session, compra: CompraCreate, current_user_id: int = None) -> Compra:
    """Crear una nueva compra"""
    compra_data = compra.model_dump(exclude={'detalles'})
    compra_data['created_by'] = current_user_id
    compra_data['updated_by'] = None
    db_compra = Compra(**compra_data)
    db.add(db_compra)
    db.commit()
    db.refresh(db_compra)
    
    # Crear detalles de compra si los hay
    if compra.detalles:
        for detalle in compra.detalles:
            # Obtener la presentación
            presentacion = db.query(Presentacion).filter(Presentacion.id == detalle.id_presentacion).first()
            if not presentacion:
                continue
                
            detalle_data = detalle.model_dump(by_alias=True)
            detalle_data['id_compra'] = db_compra.id
            
            # Si no se proporciona precio_unitario, tomarlo del precio_compra de la presentación
            if 'precio_unitario' not in detalle_data or detalle_data['precio_unitario'] is None:
                detalle_data['precio_unitario'] = presentacion.precio_compra
            
            # Si no se proporciona subtotal, calcularlo
            if detalle_data['subtotal'] is None:
                detalle_data['subtotal'] = detalle_data['precio_unitario'] * detalle.cantidad
            
            db_detalle = DetalleCompra(**detalle_data)
            db.add(db_detalle)
            
            # Actualizar el stock del producto
            producto = db.query(Producto).filter(Producto.id == presentacion.id_producto).first()
            if producto:
                # Calcular unidades totales: cantidad de presentaciones * cantidad_base de cada presentación
                unidades_agregadas = detalle.cantidad * presentacion.cantidad_base
                producto.stock_actual = (producto.stock_actual or 0) + unidades_agregadas
        
        db.commit()
    
    # Cargar las relaciones
    return db.query(Compra)\
        .options(
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor),
            joinedload(Compra.detalles).joinedload(DetalleCompra.presentacion).joinedload(Presentacion.producto)
        )\
        .filter(Compra.id == db_compra.id)\
        .first()

def actualizar_compra(db: Session, compra_id: int, compra: CompraUpdate, current_user_id: int = None) -> Optional[Compra]:
    """Actualizar una compra existente"""
    db_compra = db.query(Compra).filter(Compra.id == compra_id).first()
    
    if not db_compra:
        return None
    
    # Actualizar solo los campos proporcionados
    update_data = compra.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_compra, key, value)
    
    db_compra.fecha_edicion = datetime.datetime.utcnow()
    db_compra.updated_by = current_user_id
    db.commit()
    db.refresh(db_compra)
    
    # Cargar las relaciones
    return db.query(Compra)\
        .options(
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor),
            joinedload(Compra.detalles).joinedload(DetalleCompra.presentacion).joinedload(Presentacion.producto)
        )\
        .filter(Compra.id == db_compra.id)\
        .first()

def anular_compra(db: Session, compra_id: int) -> Optional[Compra]:
    """Anular una compra (cambio de estado a ANULADA y reversión de stock)"""
    db_compra = db.query(Compra).filter(Compra.id == compra_id).first()
    
    if not db_compra:
        return None
    
    # Verificar si la compra ya está anulada
    if db_compra.estado == "ANULADA":
        return db_compra
    
    # Revertir el stock de todos los detalles
    detalles = db.query(DetalleCompra).filter(DetalleCompra.id_compra == compra_id).all()
    for detalle in detalles:
        presentacion = db.query(Presentacion).filter(Presentacion.id == detalle.id_presentacion).first()
        if presentacion:
            producto = db.query(Producto).filter(Producto.id == presentacion.id_producto).first()
            if producto:
                unidades_revertidas = detalle.cantidad * presentacion.cantidad_base
                producto.stock_actual = (producto.stock_actual or 0) - unidades_revertidas
    
    # Cambiar el estado a ANULADA
    db_compra.estado = "ANULADA"
    db_compra.fecha_edicion = datetime.datetime.utcnow()
    db.commit()
    
    # Cargar las relaciones y devolver
    return db.query(Compra)\
        .options(
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor),
            joinedload(Compra.detalles).joinedload(DetalleCompra.presentacion).joinedload(Presentacion.producto)
        )\
        .filter(Compra.id == db_compra.id)\
        .first()

def eliminar_compra(db: Session, compra_id: int) -> bool:
    """Eliminar una compra (eliminación física)"""
    db_compra = db.query(Compra).filter(Compra.id == compra_id).first()
    
    if not db_compra:
        return False
    
    # Revertir el stock de todos los detalles antes de eliminar
    detalles = db.query(DetalleCompra).filter(DetalleCompra.id_compra == compra_id).all()
    for detalle in detalles:
        presentacion = db.query(Presentacion).filter(Presentacion.id == detalle.id_presentacion).first()
        if presentacion:
            producto = db.query(Producto).filter(Producto.id == presentacion.id_producto).first()
            if producto:
                unidades_revertidas = detalle.cantidad * presentacion.cantidad_base
                producto.stock_actual = (producto.stock_actual or 0) - unidades_revertidas
    
    db.delete(db_compra)
    db.commit()
    return True

# CRUD para DetalleCompra
def get_detalles_compra(db: Session, compra_id: int) -> List[DetalleCompra]:
    """Obtener detalles de una compra"""
    return db.query(DetalleCompra)\
        .options(joinedload(DetalleCompra.presentacion).joinedload(Presentacion.producto))\
        .filter(DetalleCompra.id_compra == compra_id)\
        .all()

def get_detalle_compra_by_id(db: Session, detalle_id: int) -> Optional[DetalleCompra]:
    """Obtener un detalle de compra por ID"""
    return db.query(DetalleCompra)\
        .options(joinedload(DetalleCompra.presentacion).joinedload(Presentacion.producto))\
        .filter(DetalleCompra.id == detalle_id)\
        .first()

def crear_detalle_compra(db: Session, detalle: DetalleCompraCreate, compra_id: int) -> DetalleCompra:
    """Crear un detalle de compra"""
    # Obtener la presentación
    presentacion = db.query(Presentacion).filter(Presentacion.id == detalle.id_presentacion).first()
    if not presentacion:
        return None
    
    detalle_data = detalle.model_dump(by_alias=True)
    detalle_data['id_compra'] = compra_id
    
    # Si no se proporciona precio_unitario, tomarlo del precio_compra de la presentación
    if 'precio_unitario' not in detalle_data or detalle_data['precio_unitario'] is None:
        detalle_data['precio_unitario'] = presentacion.precio_compra
    
    # Si no se proporciona subtotal, calcularlo
    if detalle_data['subtotal'] is None:
        detalle_data['subtotal'] = detalle_data['precio_unitario'] * detalle.cantidad
    
    db_detalle = DetalleCompra(**detalle_data)
    db.add(db_detalle)
    
    # Actualizar el stock del producto
    producto = db.query(Producto).filter(Producto.id == presentacion.id_producto).first()
    if producto:
        # Calcular unidades totales: cantidad de presentaciones * cantidad_base de cada presentación
        unidades_agregadas = detalle.cantidad * presentacion.cantidad_base
        producto.stock_actual = (producto.stock_actual or 0) + unidades_agregadas
    
    db.commit()
    db.refresh(db_detalle)
    
    return db.query(DetalleCompra)\
        .options(joinedload(DetalleCompra.presentacion).joinedload(Presentacion.producto))\
        .filter(DetalleCompra.id == db_detalle.id)\
        .first()

def actualizar_detalle_compra(db: Session, detalle_id: int, detalle: DetalleCompraUpdate) -> Optional[DetalleCompra]:
    """Actualizar un detalle de compra"""
    db_detalle = db.query(DetalleCompra).filter(DetalleCompra.id == detalle_id).first()
    
    if not db_detalle:
        return None
    
    # Obtener la cantidad anterior para ajustar el stock
    cantidad_anterior = db_detalle.cantidad
    presentacion_id_anterior = db_detalle.id_presentacion
    
    # Si se está cambiando la cantidad o la presentación, ajustar el stock
    if 'cantidad' in detalle.model_dump(exclude_unset=True) or 'id_presentacion' in detalle.model_dump(exclude_unset=True):
        # Revertir el stock de la cantidad anterior
        presentacion_anterior = db.query(Presentacion).filter(Presentacion.id == presentacion_id_anterior).first()
        if presentacion_anterior:
            producto = db.query(Producto).filter(Producto.id == presentacion_anterior.id_producto).first()
            if producto:
                unidades_revertidas = cantidad_anterior * presentacion_anterior.cantidad_base
                producto.stock_actual = (producto.stock_actual or 0) - unidades_revertidas
    
    # Actualizar los campos del detalle
    update_data = detalle.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_detalle, key, value)
    
    # Aplicar el stock con los nuevos valores
    if 'cantidad' in update_data or 'id_presentacion' in update_data:
        nueva_presentacion = db.query(Presentacion).filter(Presentacion.id == db_detalle.id_presentacion).first()
        if nueva_presentacion:
            producto = db.query(Producto).filter(Producto.id == nueva_presentacion.id_producto).first()
            if producto:
                nuevas_unidades = db_detalle.cantidad * nueva_presentacion.cantidad_base
                producto.stock_actual = (producto.stock_actual or 0) + nuevas_unidades
    
    db_detalle.fecha_edicion = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_detalle)
    
    return db.query(DetalleCompra)\
        .options(joinedload(DetalleCompra.presentacion).joinedload(Presentacion.producto))\
        .filter(DetalleCompra.id == db_detalle.id)\
        .first()

def eliminar_detalle_compra(db: Session, detalle_id: int) -> bool:
    """Eliminar un detalle de compra"""
    db_detalle = db.query(DetalleCompra).filter(DetalleCompra.id == detalle_id).first()
    
    if not db_detalle:
        return False
    
    # Revertir el stock antes de eliminar
    presentacion = db.query(Presentacion).filter(Presentacion.id == db_detalle.id_presentacion).first()
    if presentacion:
        producto = db.query(Producto).filter(Producto.id == presentacion.id_producto).first()
        if producto:
            unidades_revertidas = db_detalle.cantidad * presentacion.cantidad_base
            producto.stock_actual = (producto.stock_actual or 0) - unidades_revertidas
    
    db.delete(db_detalle)
    db.commit()
    return True
