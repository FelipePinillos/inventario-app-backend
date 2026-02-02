from sqlalchemy.orm import Session
from datetime import datetime
from app.models.marca import Marca
from app.schemas.marca import MarcaCreate, MarcaUpdate


def crear_marca_db(db: Session, marca: MarcaCreate) -> Marca:
    """Crea una nueva marca."""
    # Verificar si ya existe una marca ACTIVA con el mismo nombre
    marca_existente = db.query(Marca).filter(
        Marca.nombre == marca.nombre,
        Marca.estado == 'A'
    ).first()
    
    if marca_existente:
        raise ValueError("Ya existe una marca activa con ese nombre")
    
    db_marca = Marca(
        nombre=marca.nombre,
        estado='A',
        fecha_creacion=datetime.now().isoformat(),
        fecha_edicion=None
    )
    db.add(db_marca)
    db.commit()
    db.refresh(db_marca)
    return db_marca


def obtener_marcas_db(db: Session, incluir_inactivas: bool = False) -> list[Marca]:
    """Obtiene todas las marcas. Por defecto solo las activas."""
    query = db.query(Marca)
    
    if not incluir_inactivas:
        query = query.filter(Marca.estado == 'A')
    
    return query.order_by(Marca.id.desc()).all()


def obtener_marca_db(db: Session, marca_id: int) -> Marca | None:
    """Obtiene una marca por ID."""
    return db.query(Marca).filter(
        Marca.id == marca_id,
        Marca.estado == 'A'
    ).first()


def actualizar_marca_db(db: Session, marca_id: int, marca_update: MarcaUpdate) -> Marca:
    """Actualiza una marca."""
    db_marca = obtener_marca_db(db, marca_id)
    
    if not db_marca:
        raise ValueError("Marca no encontrada")
    
    # Actualizar solo los campos que se enviaron
    if marca_update.nombre is not None:
        # Verificar que no exista otra marca con el mismo nombre
        marca_existente = db.query(Marca).filter(
            Marca.nombre == marca_update.nombre,
            Marca.id != marca_id
        ).first()
        
        if marca_existente:
            raise ValueError("Ya existe otra marca con ese nombre")
        
        db_marca.nombre = marca_update.nombre
    
    db_marca.fecha_edicion = datetime.now().isoformat()
    db.commit()
    db.refresh(db_marca)
    return db_marca


def eliminar_marca_db(db: Session, marca_id: int) -> bool:
    """Elimina una marca (eliminación lógica)."""
    db_marca = obtener_marca_db(db, marca_id)
    
    if not db_marca:
        raise ValueError("Marca no encontrada")
    
    # No permitir eliminar la marca "NO ASIGNADA" (id=1)
    if db_marca.id == 1:
        raise ValueError("No se puede eliminar la marca 'NO ASIGNADA'")
    
    # Eliminación lógica: cambiar estado a 'I' (Inactivo)
    db_marca.estado = 'I'
    db_marca.fecha_edicion = datetime.now().isoformat()
    db.commit()
    return True
