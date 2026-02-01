from sqlalchemy.orm import Session
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate, ClienteUpdate


def crear_cliente_db(db: Session, cliente: ClienteCreate) -> Cliente:
    """Crea un nuevo cliente."""
    # Verificar si ya existe un cliente ACTIVO con el mismo DNI
    cliente_existente_dni = db.query(Cliente).filter(
        Cliente.dni == cliente.dni,
        Cliente.estado == 'A'
    ).first()
    
    if cliente_existente_dni:
        raise ValueError("Ya existe un cliente activo con ese DNI")
    
    # Verificar si ya existe un cliente ACTIVO con el mismo correo
    cliente_existente_correo = db.query(Cliente).filter(
        Cliente.correo == cliente.correo,
        Cliente.estado == 'A'
    ).first()
    
    if cliente_existente_correo:
        raise ValueError("Ya existe un cliente activo con ese correo")
    
    from datetime import datetime
    db_cliente = Cliente(
        nombre=cliente.nombre,
        apellido=cliente.apellido,
        dni=cliente.dni,
        edad=cliente.edad,
        telefono=cliente.telefono,
        correo=cliente.correo,
        sexo=cliente.sexo,
        avatar=cliente.avatar,
        estado='A',
        fecha_creacion=datetime.now().isoformat(),
        fecha_edicion=None
    )
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente


def obtener_clientes_db(db: Session, incluir_inactivos: bool = False) -> list[Cliente]:
    """Obtiene todos los clientes. Por defecto solo los activos."""
    query = db.query(Cliente)
    
    if not incluir_inactivos:
        query = query.filter(Cliente.estado == 'A')
    
    return query.order_by(Cliente.id.desc()).all()


def obtener_cliente_db(db: Session, cliente_id: int) -> Cliente | None:
    """Obtiene un cliente por ID."""
    return db.query(Cliente).filter(
        Cliente.id == cliente_id,
        Cliente.estado == 'A'
    ).first()


def obtener_cliente_por_dni_db(db: Session, dni: str) -> Cliente | None:
    """Obtiene un cliente por DNI."""
    return db.query(Cliente).filter(
        Cliente.dni == dni,
        Cliente.estado == 'A'
    ).first()


def actualizar_cliente_db(db: Session, cliente_id: int, cliente_update: ClienteUpdate) -> Cliente:
    """Actualiza un cliente."""
    db_cliente = obtener_cliente_db(db, cliente_id)
    
    if not db_cliente:
        raise ValueError("Cliente no encontrado")
    
    # Validar DNI único si se está actualizando
    if cliente_update.dni is not None:
        cliente_existente = db.query(Cliente).filter(
            Cliente.dni == cliente_update.dni,
            Cliente.id != cliente_id,
            Cliente.estado == 'A'
        ).first()
        
        if cliente_existente:
            raise ValueError("Ya existe otro cliente activo con ese DNI")
        
        db_cliente.dni = cliente_update.dni
    
    # Validar correo único si se está actualizando
    if cliente_update.correo is not None:
        cliente_existente = db.query(Cliente).filter(
            Cliente.correo == cliente_update.correo,
            Cliente.id != cliente_id,
            Cliente.estado == 'A'
        ).first()
        
        if cliente_existente:
            raise ValueError("Ya existe otro cliente activo con ese correo")
        
        db_cliente.correo = cliente_update.correo
    
    # Actualizar otros campos
    if cliente_update.nombre is not None:
        db_cliente.nombre = cliente_update.nombre
    if cliente_update.apellido is not None:
        db_cliente.apellido = cliente_update.apellido
    if cliente_update.edad is not None:
        db_cliente.edad = cliente_update.edad
    if cliente_update.telefono is not None:
        db_cliente.telefono = cliente_update.telefono
    if cliente_update.sexo is not None:
        db_cliente.sexo = cliente_update.sexo
    if cliente_update.avatar is not None:
        db_cliente.avatar = cliente_update.avatar
    from datetime import datetime
    db_cliente.fecha_edicion = datetime.now().isoformat()
    db.commit()
    db.refresh(db_cliente)
    return db_cliente


def eliminar_cliente_db(db: Session, cliente_id: int) -> bool:
    """Elimina un cliente (eliminación lógica)."""
    db_cliente = obtener_cliente_db(db, cliente_id)
    
    if not db_cliente:
        raise ValueError("Cliente no encontrado")
    
    # Eliminación lógica: cambiar estado a 'I' (Inactivo)
    db_cliente.estado = 'I'
    db.commit()
    return True
