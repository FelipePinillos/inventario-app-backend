from sqlalchemy.orm import Session
from datetime import datetime
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate


def crear_categoria_db(db: Session, categoria: CategoriaCreate) -> Categoria:
    """Crea una nueva categoría."""
    # Verificar si ya existe una categoría ACTIVA con el mismo nombre
    categoria_existente = db.query(Categoria).filter(
        Categoria.nombre == categoria.nombre,
        Categoria.estado == 'A'
    ).first()
    
    if categoria_existente:
        raise ValueError("Ya existe una categoría activa con ese nombre")
    
    db_categoria = Categoria(
        nombre=categoria.nombre,
        estado='A'
    )
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


def obtener_categorias_db(db: Session, incluir_inactivas: bool = False) -> list[Categoria]:
    """Obtiene todas las categorías. Por defecto solo las activas."""
    query = db.query(Categoria)
    
    if not incluir_inactivas:
        query = query.filter(Categoria.estado == 'A')
    
    return query.order_by(Categoria.id.desc()).all()


def obtener_categoria_db(db: Session, categoria_id: int) -> Categoria | None:
    """Obtiene una categoría por ID."""
    return db.query(Categoria).filter(
        Categoria.id == categoria_id,
        Categoria.estado == 'A'
    ).first()


def actualizar_categoria_db(db: Session, categoria_id: int, categoria_update: CategoriaUpdate) -> Categoria:
    """Actualiza una categoría."""
    db_categoria = obtener_categoria_db(db, categoria_id)
    
    if not db_categoria:
        raise ValueError("Categoría no encontrada")
    
    # Actualizar solo los campos que se enviaron
    if categoria_update.nombre is not None:
        # Verificar que no exista otra categoría con el mismo nombre
        categoria_existente = db.query(Categoria).filter(
            Categoria.nombre == categoria_update.nombre,
            Categoria.id != categoria_id
        ).first()
        
        if categoria_existente:
            raise ValueError("Ya existe otra categoría con ese nombre")
        
        db_categoria.nombre = categoria_update.nombre
    
    db_categoria.fecha_edicion = datetime.now()
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


def eliminar_categoria_db(db: Session, categoria_id: int) -> bool:
    """Elimina una categoría (eliminación lógica)."""
    db_categoria = obtener_categoria_db(db, categoria_id)
    
    if not db_categoria:
        raise ValueError("Categoría no encontrada")
    
    # No permitir eliminar la categoría "NO ASIGNADA" (id=1)
    if db_categoria.id == 1:
        raise ValueError("No se puede eliminar la categoría 'NO ASIGNADA'")
    
    # Eliminación lógica: cambiar estado a 'I' (Inactivo)
    db_categoria.estado = 'I'
    db_categoria.fecha_edicion = datetime.now()
    db.commit()
    return True