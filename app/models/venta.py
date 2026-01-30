from sqlalchemy import Column, Integer, DateTime, DECIMAL, ForeignKey, String
from sqlalchemy.orm import relationship
from app.database import Base

# Importar los modelos relacionados para que SQLAlchemy los encuentre
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.models.producto import Producto
from app.models.presentacion import Presentacion

class Venta(Base):
    __tablename__ = "ventas"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_cliente = Column(Integer, ForeignKey("cliente.id"), nullable=True)
    fecha = Column(DateTime, nullable=True)
    totalcondescuento = Column(DECIMAL(10, 2), nullable=True)
    descuento = Column(DECIMAL(10, 2), nullable=True)
    totalsindescuento = Column(DECIMAL(10, 2), nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id"), nullable=True)
    estado = Column(String(15), default="CONFIRMADA", nullable=False)
    
    # Relaciones
    cliente = relationship("Cliente")
    usuario = relationship("Usuario")
    detalles = relationship("DetalleVenta", back_populates="venta", cascade="all, delete-orphan")

class DetalleVenta(Base):
    __tablename__ = "detalle_venta"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_venta = Column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"), nullable=True)
    id_producto = Column(Integer, ForeignKey("producto.id"), nullable=True)
    id_presentacion = Column(Integer, ForeignKey("presentaciones.id"), nullable=True)
    cantidad = Column(Integer, nullable=True)
    precio_unitario = Column(DECIMAL(10, 2), nullable=True)
    subtotal = Column(DECIMAL(10, 2), nullable=True)
    
    # Relaciones
    venta = relationship("Venta", back_populates="detalles")
    producto = relationship("Producto")
    presentacion = relationship("Presentacion")
