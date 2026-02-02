from sqlalchemy.orm import Session, joinedload
from app.models.compra import Compra, DetalleCompra
from app.schemas.compra import CompraCreate, CompraUpdate, DetalleCompraCreate, DetalleCompraUpdate
from typing import Optional, List
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
            joinedload(Compra.detalles)
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
            joinedload(Compra.detalles).joinedload(DetalleCompra.presentacion)
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
            joinedload(Compra.detalles)
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
            joinedload(Compra.detalles)
        )\
        .filter(Compra.id_usuario == usuario_id)\
        .order_by(Compra.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def crear_compra(db: Session, compra: CompraCreate) -> Compra:
    """Crear una nueva compra"""
    compra_data = compra.model_dump(exclude={'detalles'})
    db_compra = Compra(**compra_data)
    db.add(db_compra)
    db.commit()
    db.refresh(db_compra)
    
    # Crear detalles de compra si los hay
    if compra.detalles:
        for detalle in compra.detalles:
            detalle_data = detalle.model_dump()
            detalle_data['id_compra'] = db_compra.id
            db_detalle = DetalleCompra(**detalle_data)
            db.add(db_detalle)
        
        db.commit()
    
    # Cargar las relaciones
    return db.query(Compra)\
        .options(
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor),
            joinedload(Compra.detalles).joinedload(DetalleCompra.presentacion)
        )\
        .filter(Compra.id == db_compra.id)\
        .first()

def actualizar_compra(db: Session, compra_id: int, compra: CompraUpdate) -> Optional[Compra]:
    """Actualizar una compra existente"""
    db_compra = db.query(Compra).filter(Compra.id == compra_id).first()
    
    if not db_compra:
        return None
    
    # Actualizar solo los campos proporcionados
    update_data = compra.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_compra, key, value)
    
    db_compra.fecha_edicion = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_compra)
    
    # Cargar las relaciones
    return db.query(Compra)\
        .options(
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor),
            joinedload(Compra.detalles).joinedload(DetalleCompra.presentacion)
        )\
        .filter(Compra.id == db_compra.id)\
        .first()

def eliminar_compra(db: Session, compra_id: int) -> bool:
    """Eliminar una compra (eliminación física)"""
    db_compra = db.query(Compra).filter(Compra.id == compra_id).first()
    
    if not db_compra:
        return False
    
    db.delete(db_compra)
    db.commit()
    return True

# CRUD para DetalleCompra
def get_detalles_compra(db: Session, compra_id: int) -> List[DetalleCompra]:
    """Obtener detalles de una compra"""
    return db.query(DetalleCompra)\
        .options(joinedload(DetalleCompra.presentacion))\
        .filter(DetalleCompra.id_compra == compra_id)\
        .all()

def get_detalle_compra_by_id(db: Session, detalle_id: int) -> Optional[DetalleCompra]:
    """Obtener un detalle de compra por ID"""
    return db.query(DetalleCompra)\
        .options(joinedload(DetalleCompra.presentacion))\
        .filter(DetalleCompra.id == detalle_id)\
        .first()

def crear_detalle_compra(db: Session, detalle: DetalleCompraCreate, compra_id: int) -> DetalleCompra:
    """Crear un detalle de compra"""
    detalle_data = detalle.model_dump()
    detalle_data['id_compra'] = compra_id
    db_detalle = DetalleCompra(**detalle_data)
    db.add(db_detalle)
    db.commit()
    db.refresh(db_detalle)
    
    return db.query(DetalleCompra)\
        .options(joinedload(DetalleCompra.presentacion))\
        .filter(DetalleCompra.id == db_detalle.id)\
        .first()

def actualizar_detalle_compra(db: Session, detalle_id: int, detalle: DetalleCompraUpdate) -> Optional[DetalleCompra]:
    """Actualizar un detalle de compra"""
    db_detalle = db.query(DetalleCompra).filter(DetalleCompra.id == detalle_id).first()
    
    if not db_detalle:
        return None
    
    update_data = detalle.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_detalle, key, value)
    
    db_detalle.fecha_edicion = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_detalle)
    
    return db.query(DetalleCompra)\
        .options(joinedload(DetalleCompra.presentacion))\
        .filter(DetalleCompra.id == db_detalle.id)\
        .first()

def eliminar_detalle_compra(db: Session, detalle_id: int) -> bool:
    """Eliminar un detalle de compra"""
    db_detalle = db.query(DetalleCompra).filter(DetalleCompra.id == detalle_id).first()
    
    if not db_detalle:
        return False
    
    db.delete(db_detalle)
    db.commit()
    return True
