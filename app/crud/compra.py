from sqlalchemy.orm import Session, joinedload
from app.models.compra import Compra
from app.schemas.compra import CompraCreate, CompraUpdate
from typing import Optional, List

def get_compras(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[Compra]:
    """Obtener lista de compras con relaciones, ordenadas por ID descendente"""
    return db.query(Compra)\
        .options(
            joinedload(Compra.estado_pago),
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor)
        )\
        .order_by(Compra.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_compra_by_id(db: Session, compra_id: int) -> Optional[Compra]:
    """Obtener una compra por ID con sus relaciones"""
    return db.query(Compra)\
        .options(
            joinedload(Compra.estado_pago),
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor)
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
            joinedload(Compra.estado_pago),
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor)
        )\
        .filter(Compra.id_proveedor == proveedor_id)\
        .order_by(Compra.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_compras_by_estado(
    db: Session, 
    estado_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Compra]:
    """Obtener compras por estado de pago"""
    return db.query(Compra)\
        .options(
            joinedload(Compra.estado_pago),
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor)
        )\
        .filter(Compra.id_estado == estado_id)\
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
            joinedload(Compra.estado_pago),
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor)
        )\
        .filter(Compra.id_usuario == usuario_id)\
        .order_by(Compra.id.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def crear_compra(db: Session, compra: CompraCreate) -> Compra:
    """Crear una nueva compra"""
    db_compra = Compra(**compra.model_dump())
    db.add(db_compra)
    db.commit()
    db.refresh(db_compra)
    
    # Cargar las relaciones
    return db.query(Compra)\
        .options(
            joinedload(Compra.estado_pago),
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor)
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
    
    db.commit()
    db.refresh(db_compra)
    
    # Cargar las relaciones
    return db.query(Compra)\
        .options(
            joinedload(Compra.estado_pago),
            joinedload(Compra.usuario),
            joinedload(Compra.proveedor)
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
