from sqlalchemy.orm import Session, joinedload
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, TipoUsuarioResponse
from app.utils import hash_password
from sqlalchemy import or_ # importar or_ para consultas complejas

# el crud es el que utiliza los modelos creados con sqlAlchemy, que es como un orm
# nos permite crear, leer, actualizar y eliminar usuarios en la base de datos
# es decir, las operaciones básicas de una base de datos
# asi separamos la logica de negocio de la logica de acceso a datos


# Hacer esto:
# Usuario(**usuario.dict())

# Es igual que hacer asi:
# Usuario(
#     nombre=usuario.nombre,
#     apellido=usuario.apellido,
#     dni=usuario.dni,
#     password=usuario.password,
#     id_tipo_usuario=usuario.id_tipo_usuario
# )

# el objetivo de esto es simplificar la creación de instancias de la clase Usuario
# y pasar de un esquema Pydantic a un modelo SQLAlchemy.
def crear_usuario_db(db: Session, usuario: UsuarioCreate) ->Usuario:

    existe = db.query(Usuario).filter(
        Usuario.dni == usuario.dni
    ).first()

    if existe:
        raise ValueError("Ya existe un usuario con ese DNI")
    

    # db_usuario = Usuario(**usuario.dict())
    db_usuario = Usuario(
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        dni=usuario.dni,
        contrasena=usuario.password,  # TEMPORAL: Sin hashear (TODO: usar hash_password en producción)
        id_tipo_usuario=usuario.id_tipo_usuario
    )

    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


def obtener_usuarios_db(db: Session) -> Usuario | None:
    return db.query(Usuario).options(joinedload(Usuario.tipo_usuario)).order_by(Usuario.id.desc()).all()


def obtener_usuario_db(db: Session, usuario_id: int = None, usuario: str = None):
    """Obtener usuario por ID o por nombre."""
    if usuario_id:
        return db.query(Usuario).filter(Usuario.id == usuario_id).first()
    elif usuario:
        return db.query(Usuario).filter(Usuario.nombre == usuario).first()
    return None



def actualizar_usuario_db(db: Session, usuario_id: int, datos):
    usuario = obtener_usuario_db(db, usuario_id)

    if usuario:
        data = datos.dict(exclude_unset=True)
        for key, value in data.items():
            if key == "password":
                if value:  # Solo actualizar si se envía un valor no vacío
                    usuario.contrasena = value
            else:
                setattr(usuario, key, value)

        db.commit()
        db.refresh(usuario)

    return usuario


def eliminar_usuario_db(db: Session, usuario_id: int):
    usuario = obtener_usuario_db(db, usuario_id)

    if usuario:
        db.delete(usuario)
        db.commit()

    return usuario


