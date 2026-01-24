from sqlalchemy.orm import Session, joinedload
from app.models.venta import Venta, DetalleVenta
from app.models.producto import Producto
from app.models.presentacion import Presentacion
from app.schemas.venta import VentaCreate, VentaUpdate
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

def get_ventas(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[Venta]:
    """Obtener lista de ventas con relaciones, ordenadas por ID descendente"""
    return db.query(Venta)\
        .options(
            joinedload(Venta.cliente),
            joinedload(Venta.usuario),
            joinedload(Venta.detalles).joinedload(DetalleVenta.producto),
            joinedload(Venta.detalles).joinedload(DetalleVenta.presentacion)
        )\
        .order_by(Venta.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_venta_by_id(db: Session, venta_id: int) -> Optional[Venta]:
    """Obtener una venta por ID con sus relaciones"""
    return db.query(Venta)\
        .options(
            joinedload(Venta.cliente),
            joinedload(Venta.usuario),
            joinedload(Venta.detalles).joinedload(DetalleVenta.producto),
            joinedload(Venta.detalles).joinedload(DetalleVenta.presentacion)
        )\
        .filter(Venta.id == venta_id)\
        .first()

def get_ventas_by_cliente(
    db: Session, 
    cliente_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Venta]:
    """Obtener ventas por cliente"""
    return db.query(Venta)\
        .options(
            joinedload(Venta.cliente),
            joinedload(Venta.usuario),
            joinedload(Venta.detalles).joinedload(DetalleVenta.producto),
            joinedload(Venta.detalles).joinedload(DetalleVenta.presentacion)
        )\
        .filter(Venta.id_cliente == cliente_id)\
        .order_by(Venta.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_ventas_by_usuario(
    db: Session, 
    usuario_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Venta]:
    """Obtener ventas por usuario"""
    return db.query(Venta)\
        .options(
            joinedload(Venta.cliente),
            joinedload(Venta.usuario),
            joinedload(Venta.detalles).joinedload(DetalleVenta.producto),
            joinedload(Venta.detalles).joinedload(DetalleVenta.presentacion)
        )\
        .filter(Venta.id_usuario == usuario_id)\
        .order_by(Venta.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_ventas_by_fecha(
    db: Session,
    fecha_inicio,
    fecha_fin,
    skip: int = 0,
    limit: int = 100
) -> List[Venta]:
    """Obtener ventas por rango de fechas"""
    return db.query(Venta)\
        .options(
            joinedload(Venta.cliente),
            joinedload(Venta.usuario),
            joinedload(Venta.detalles).joinedload(DetalleVenta.producto),
            joinedload(Venta.detalles).joinedload(DetalleVenta.presentacion)
        )\
        .filter(Venta.Fecha >= fecha_inicio, Venta.Fecha <= fecha_fin)\
        .order_by(Venta.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def crear_venta(db: Session, venta: VentaCreate) -> Venta:
    """
    Crear una nueva venta con sus detalles
    - Calcula automáticamente los totales
    - Descuenta el stock según cantidad_base de cada presentación
    """
    try:
        # 1. Calcular totales a partir de los detalles
        total_sin_descuento = Decimal(0)
        for detalle in venta.detalles:
            total_sin_descuento += detalle.subtotal
        
        descuento_aplicado = venta.descuento or Decimal(0)
        total_con_descuento = total_sin_descuento - descuento_aplicado
        
        # 2. Crear la venta
        db_venta = Venta(
            id_cliente=venta.id_cliente,
            Fecha=venta.Fecha or datetime.now(),
            descuento=descuento_aplicado,
            TotalSinDescuento=total_sin_descuento,
            TotalConDescuento=total_con_descuento,
            id_usuario=venta.id_usuario,
            estado=venta.estado or "CONFIRMADA"
        )
        db.add(db_venta)
        db.flush()  # Para obtener el ID de la venta
        
        # 3. Crear los detalles y descontar stock
        for detalle_data in venta.detalles:
            # Verificar que la presentación existe
            presentacion = db.query(Presentacion).filter(
                Presentacion.id == detalle_data.id_presentacion
            ).first()
            
            if not presentacion:
                raise ValueError(f"Presentación con ID {detalle_data.id_presentacion} no existe")
            
            # Verificar que el producto existe
            producto = db.query(Producto).filter(
                Producto.id == detalle_data.id_producto
            ).first()
            
            if not producto:
                raise ValueError(f"Producto con ID {detalle_data.id_producto} no existe")
            
            # Calcular unidades a descontar = cantidad vendida * cantidad_base de la presentación
            unidades_a_descontar = detalle_data.cantidad * presentacion.cantidad_base
            
            # Verificar stock suficiente
            if producto.stock_actual < unidades_a_descontar:
                raise ValueError(
                    f"Stock insuficiente para {producto.nombre}. "
                    f"Disponible: {producto.stock_actual}, Requerido: {unidades_a_descontar}"
                )
            
            # Descontar del stock
            producto.stock_actual -= unidades_a_descontar
            
            # Crear detalle de venta
            db_detalle = DetalleVenta(
                id_venta=db_venta.id,
                id_producto=detalle_data.id_producto,
                id_presentacion=detalle_data.id_presentacion,
                cantidad=detalle_data.cantidad,
                precio_unitario=detalle_data.precio_unitario,
                subtotal=detalle_data.subtotal
            )
            db.add(db_detalle)
        
        db.commit()
        db.refresh(db_venta)
        
        # Cargar las relaciones
        return get_venta_by_id(db, db_venta.id)
        
    except Exception as e:
        db.rollback()
        raise e

def actualizar_venta(db: Session, venta_id: int, venta: VentaUpdate) -> Optional[Venta]:
    """
    Actualizar una venta existente (solo campos principales, no detalles)
    """
    db_venta = db.query(Venta).filter(Venta.id == venta_id).first()
    
    if not db_venta:
        return None
    
    # Actualizar solo los campos proporcionados
    update_data = venta.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_venta, key, value)
    
    db.commit()
    
    # Cargar las relaciones
    return get_venta_by_id(db, venta_id)

def eliminar_venta(db: Session, venta_id: int) -> bool:
    """
    Eliminar una venta (eliminación física)
    IMPORTANTE: Esto NO restaura el stock. Considera cambiar a estado="CANCELADA"
    """
    db_venta = db.query(Venta).filter(Venta.id == venta_id).first()
    
    if not db_venta:
        return False
    
    db.delete(db_venta)
    db.commit()
    return True

def cancelar_venta(db: Session, venta_id: int) -> Optional[Venta]:
    """
    Cancelar una venta (cambiar estado a CANCELADA y restaurar stock)
    """
    db_venta = get_venta_by_id(db, venta_id)
    
    if not db_venta:
        return None
    
    if db_venta.estado == "CANCELADA":
        return db_venta  # Ya está cancelada
    
    try:
        # Restaurar stock por cada detalle
        for detalle in db_venta.detalles:
            producto = db.query(Producto).filter(Producto.id == detalle.id_producto).first()
            presentacion = db.query(Presentacion).filter(Presentacion.id == detalle.id_presentacion).first()
            
            if producto and presentacion:
                unidades_a_restaurar = detalle.cantidad * presentacion.cantidad_base
                producto.stock_actual += unidades_a_restaurar
        
        # Cambiar estado
        db_venta.estado = "CANCELADA"
        
        db.commit()
        return get_venta_by_id(db, venta_id)
        
    except Exception as e:
        db.rollback()
        raise e
