from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Presentacion(Base):
    __tablename__ = "presentaciones"

    id = Column(Integer, primary_key=True, index=True)
    id_producto = Column(Integer, ForeignKey("producto.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String(100), nullable=False)  # Ej: "Unidad", "Paquete x6", "Caja x12"
    cantidad_base = Column(Integer, nullable=False)  # Cantidad de unidades base que contiene
    precio = Column(Float, nullable=False)  # Precio de esta presentación
    estado = Column(String(10), default='A')  # A = Activo, I = Inactivo
    fecha_creacion = Column(DateTime, default=datetime.now)
    
    # Relación con producto
    producto = relationship("Producto", backref="presentaciones")
