from sqlalchemy import Column, Integer, Date, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

# Importar los modelos relacionados para que SQLAlchemy los encuentre
from app.models.estadoPago import EstadoPago
from app.models.usuario import Usuario
from app.models.proveedor import Proveedor

class Compra(Base):
    __tablename__ = "compras"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha_compra = Column(Date, nullable=True)
    fecha_entrega = Column(Date, nullable=True)
    TotalConDescuento = Column(DECIMAL(10, 2), nullable=True)
    descuento = Column(DECIMAL(10, 2), nullable=False)
    TotalSinDescuento = Column(DECIMAL(10, 2), nullable=False)
    id_estado = Column(Integer, ForeignKey("estado_pago.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id"), nullable=True)
    id_proveedor = Column(Integer, ForeignKey("proveedor.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    
    # Relaciones
    estado_pago = relationship("EstadoPago")
    usuario = relationship("Usuario")
    proveedor = relationship("Proveedor")
