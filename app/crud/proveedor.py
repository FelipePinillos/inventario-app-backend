from sqlalchemy.orm import Session
from app.models.proveedor import Proveedor
from app.schemas.proveedor import ProveedorCreate, ProveedorUpdate


def crear_proveedor_db(db: Session, proveedor: ProveedorCreate, current_user_id: int = None) -> Proveedor:
    """Crea un nuevo proveedor."""
    # Verificar si ya existe un proveedor ACTIVO con el mismo RUC
    proveedor_existente = db.query(Proveedor).filter(
        Proveedor.ruc == proveedor.ruc,
        Proveedor.estado == 'A'
    ).first()
    
    if proveedor_existente:
        raise ValueError("Ya existe un proveedor activo con ese RUC")
    
    from datetime import datetime
    db_proveedor = Proveedor(
        razon_social=proveedor.razon_social,
        ruc=proveedor.ruc,
        telefono=proveedor.telefono,
        correo=proveedor.correo,
        direccion=proveedor.direccion,
        avatar=proveedor.avatar,
        estado='A',
        fecha_creacion=datetime.now().isoformat(),
        fecha_edicion=None,
        created_by=current_user_id,
        updated_by=None
    )
    db.add(db_proveedor)
    db.commit()
    db.refresh(db_proveedor)
    return db_proveedor


def obtener_proveedores_db(db: Session, incluir_inactivos: bool = False) -> list[Proveedor]:
    """Obtiene todos los proveedores. Por defecto solo los activos."""
    query = db.query(Proveedor)
    
    if not incluir_inactivos:
        query = query.filter(Proveedor.estado == 'A')
    
    return query.order_by(Proveedor.id.desc()).all()


def obtener_proveedor_db(db: Session, proveedor_id: int) -> Proveedor | None:
    """Obtiene un proveedor por ID."""
    return db.query(Proveedor).filter(
        Proveedor.id == proveedor_id,
        Proveedor.estado == 'A'
    ).first()


def obtener_proveedor_por_ruc_db(db: Session, ruc: int) -> Proveedor | None:
    """Obtiene un proveedor por RUC."""
    return db.query(Proveedor).filter(
        Proveedor.ruc == ruc,
        Proveedor.estado == 'A'
    ).first()


def actualizar_proveedor_db(db: Session, proveedor_id: int, proveedor_update: ProveedorUpdate, current_user_id: int = None) -> Proveedor:
    """Actualiza un proveedor."""
    db_proveedor = obtener_proveedor_db(db, proveedor_id)
    
    if not db_proveedor:
        raise ValueError("Proveedor no encontrado")
    
    # Validar RUC único si se está actualizando
    if proveedor_update.ruc is not None:
        proveedor_existente = db.query(Proveedor).filter(
            Proveedor.ruc == proveedor_update.ruc,
            Proveedor.id != proveedor_id,
            Proveedor.estado == 'A'
        ).first()
        
        if proveedor_existente:
            raise ValueError("Ya existe otro proveedor activo con ese RUC")
        
        db_proveedor.ruc = proveedor_update.ruc
    
    # Actualizar otros campos
    if proveedor_update.razon_social is not None:
        db_proveedor.razon_social = proveedor_update.razon_social
    if proveedor_update.telefono is not None:
        db_proveedor.telefono = proveedor_update.telefono
    if proveedor_update.correo is not None:
        db_proveedor.correo = proveedor_update.correo
    if proveedor_update.direccion is not None:
        db_proveedor.direccion = proveedor_update.direccion
    if proveedor_update.avatar is not None:
        db_proveedor.avatar = proveedor_update.avatar
    
    from datetime import datetime
    db_proveedor.fecha_edicion = datetime.now().isoformat()
    db_proveedor.updated_by = current_user_id
    db.commit()
    db.refresh(db_proveedor)
    return db_proveedor


def eliminar_proveedor_db(db: Session, proveedor_id: int) -> bool:
    """Elimina un proveedor (eliminación lógica)."""
    db_proveedor = obtener_proveedor_db(db, proveedor_id)
    
    if not db_proveedor:
        raise ValueError("Proveedor no encontrado")
    
    # Eliminación lógica: cambiar estado a 'I' (Inactivo)
    db_proveedor.estado = 'I'
    db.commit()
    return True
