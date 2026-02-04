from sqlalchemy import Column, Integer, Date, DECIMAL, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

# Importar los modelos relacionados para que SQLAlchemy los encuentre
from app.models.usuario import Usuario
from app.models.proveedor import Proveedor

class Compra(Base):
    __tablename__ = "compras"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha_compra = Column(DateTime, nullable=True)
    fecha_entrega = Column(DateTime, nullable=True)
    totalcondescuento = Column(DECIMAL(10, 2), nullable=True)
    descuento = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    totalsindescuento = Column(DECIMAL(10, 2), nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuario.id"), nullable=True)
    id_proveedor = Column(Integer, ForeignKey("proveedor.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    estado = Column(String(15), default="CONFIRMADA", nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    fecha_edicion = Column(DateTime, nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario")
    proveedor = relationship("Proveedor")
    detalles = relationship("DetalleCompra", back_populates="compra")

class DetalleCompra(Base):
    __tablename__ = "detalle_compra"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_compra = Column(Integer, ForeignKey("compras.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    id_presentacion = Column(Integer, ForeignKey("presentaciones.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    fecha_edicion = Column(DateTime, nullable=True)
    
    # Relaciones
    compra = relationship("Compra", back_populates="detalles")
    presentacion = relationship("Presentacion")
