from sqlalchemy import Column, Integer, String, BigInteger
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
