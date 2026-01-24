from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Marca(Base):
    __tablename__ = "marca"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, index=True)
    estado = Column(String(1), default='A')  # A = Activo, I = Inactivo
    fecha_creacion = Column(DateTime, default=datetime.now)
    fecha_edicion = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    # productos = relationship("Producto", back_populates="marca")  # Descomentar si hay relación con productos
