from sqlalchemy import Column, Integer, DateTime, DECIMAL, ForeignKey, String
from sqlalchemy.orm import relationship
from app.database import Base

# Importar los modelos relacionados para que SQLAlchemy los encuentre
from app.models.cliente import Cliente
from app.models.usuario import Usuario
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
    fecha_creacion = Column(String(25), nullable=False)
    fecha_edicion = Column(String(25), nullable=True)
    
    # Relaciones
    cliente = relationship("Cliente")
    usuario = relationship("Usuario")
    detalles = relationship("DetalleVenta", back_populates="venta", cascade="all, delete-orphan")

class DetalleVenta(Base):
    __tablename__ = "detalle_venta"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_venta = Column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"), nullable=True)
    id_presentacion = Column(Integer, ForeignKey("presentaciones.id"), nullable=True)
    cantidad = Column(Integer, nullable=True)
    precio_unitario = Column(DECIMAL(10, 2), nullable=True)
    subtotal = Column(DECIMAL(10, 2), nullable=True)
    
    # Relaciones
    venta = relationship("Venta", back_populates="detalles")
    presentacion = relationship("Presentacion")
    
    @property
    def producto(self):
        """Obtener el producto a través de la presentación"""
        if self.presentacion:
            return self.presentacion.producto
        return None
