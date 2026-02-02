from sqlalchemy import Column, Integer, String, Date, BigInteger
from app.database import Base


class Cliente(Base):
    __tablename__ = "cliente"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), index=True)
    apellido = Column(String(100), index=True)
    dni = Column(String(20), unique=True, index=True)
    telefono = Column(BigInteger)  # Número entero grande
    correo = Column(String(100), unique=True, index=True)
    estado = Column(String(1), default='A')  # A = Activo, I = Inactivo
    fecha_creacion = Column(String(25), nullable=False)
    fecha_edicion = Column(String(25), nullable=True)
