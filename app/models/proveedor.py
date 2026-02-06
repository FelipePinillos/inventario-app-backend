from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey
from app.database import Base


class Proveedor(Base):
    __tablename__ = "proveedor"

    id = Column(Integer, primary_key=True, index=True)
    razon_social = Column(String(250), index=True)
    ruc = Column(BigInteger, unique=True, index=True)
    telefono = Column(BigInteger)
    correo = Column(String(100))
    direccion = Column(String(250))
    avatar = Column(String(250), nullable=True)
    estado = Column(String(1), default='A')  # A = Activo, I = Inactivo
    fecha_creacion = Column(String(25), nullable=False)
    fecha_edicion = Column(String(25), nullable=True)
    created_by = Column(Integer, ForeignKey("usuario.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuario.id"), nullable=True)
