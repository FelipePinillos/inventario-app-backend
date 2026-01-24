"""  
CRUD operations para Presentaciones.
"""
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.models.presentacion import Presentacion
from app.schemas.presentacion import PresentacionCreate, PresentacionUpdate


def get_presentaciones(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    id_producto: Optional[int] = None
) -> List[Presentacion]:
    """Obtener lista de presentaciones con filtros opcionales."""
    query = db.query(Presentacion).options(joinedload(Presentacion.producto))
    
    if id_producto:
        query = query.filter(Presentacion.id_producto == id_producto)
    
    return query.offset(skip).limit(limit).all()


def get_presentacion(db: Session, presentacion_id: int) -> Optional[Presentacion]:
    """Obtener una presentación por ID."""
    return db.query(Presentacion).options(
        joinedload(Presentacion.producto)
    ).filter(Presentacion.id == presentacion_id).first()


def create_presentacion(db: Session, presentacion: PresentacionCreate) -> Presentacion:
    """Crear una nueva presentación."""
    db_presentacion = Presentacion(**presentacion.model_dump())
    db.add(db_presentacion)
    db.commit()
    db.refresh(db_presentacion)
    return db_presentacion


def update_presentacion(
    db: Session, 
    presentacion_id: int, 
    presentacion: PresentacionUpdate
) -> Optional[Presentacion]:
    """Actualizar una presentación existente."""
    db_presentacion = get_presentacion(db, presentacion_id)
    
    if not db_presentacion:
        return None
    
    # Actualizar solo los campos proporcionados
    update_data = presentacion.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_presentacion, field, value)
    
    db.commit()
    db.refresh(db_presentacion)
    return db_presentacion


def delete_presentacion(db: Session, presentacion_id: int) -> bool:
    """Eliminar una presentación."""
    db_presentacion = get_presentacion(db, presentacion_id)
    
    if not db_presentacion:
        return False
    
    db.delete(db_presentacion)
    db.commit()
    return True


def get_presentaciones_by_producto(db: Session, id_producto: int) -> List[Presentacion]:
    """Obtener todas las presentaciones de un producto específico."""
    return db.query(Presentacion).options(
        joinedload(Presentacion.producto)
    ).filter(
        Presentacion.id_producto == id_producto,
        Presentacion.estado == 'A'
    ).all()
