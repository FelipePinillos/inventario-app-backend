from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.tipoUsuario import TipoUsuario


# un modelo es una representación de un tabla en la base de datos
# que define cómo se estructuran los datos
# todo eso gracias a sqlalchemy
# back_populates es para que la relación sea bidireccional

class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), index=True)
    apellido = Column(String(100), index=True)
    dni = Column(String(100), unique=True, index=True)
    contrasena = Column(String(200), nullable=False)
    estado = Column(String(1), default='A', nullable=False)  # 'A' = Activo, 'I' = Inactivo
    fecha_creacion = Column(String(25), nullable=False)
    fecha_edicion = Column(String(25), nullable=True)
    created_by = Column(Integer, ForeignKey("usuario.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuario.id"), nullable=True)

    id_tipo_usuario = Column(Integer, ForeignKey("tipo_usuario.id"), nullable=False)
    tipo_usuario = relationship("TipoUsuario", back_populates="usuarios")
