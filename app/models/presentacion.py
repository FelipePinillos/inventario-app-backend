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
    precio_venta = Column(Float, nullable=False)  # Precio de venta de esta presentación
    precio_compra = Column(Float, nullable=False)  # Precio de compra de esta presentación
    estado = Column(String(10), default='A')  # A = Activo, I = Inactivo
    fecha_creacion = Column(String(25), nullable=False)
    fecha_edicion = Column(String(25), nullable=True)
    
    # Relación con producto
    producto = relationship("Producto", backref="presentaciones")
