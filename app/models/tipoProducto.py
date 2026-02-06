from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class TipoProducto(Base):
    __tablename__ = "tipo_producto"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, index=True)
    estado = Column(String(1), default='A')  # A = Activo, I = Inactivo
    fecha_creacion = Column(String(25), nullable=False)
    fecha_edicion = Column(String(25), nullable=True)
    created_by = Column(Integer, ForeignKey("usuario.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuario.id"), nullable=True)
    # productos = relationship("Producto", back_populates="tipo_producto")  # Descomentar si hay relación con productos
