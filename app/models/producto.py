from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Producto(Base):
    __tablename__ = "producto"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, index=True)
    nombre = Column(String(100), index=True)
    unidad_base = Column(String(50), default='unidad')  # Unidad de medida base
    adicional = Column(String(250))  # Descripción adicional
    stock_minimo = Column(Integer)
    stock_actual = Column(Integer)
    stock_maximo = Column(Integer, nullable=True)
    avatar = Column(String(250), nullable=True)  # URL de la imagen
    estado = Column(String(1), default='A')  # A = Activo, I = Inactivo
    fecha_creacion = Column(String(25), nullable=False)
    fecha_edicion = Column(String(25), nullable=True)
    
    # Claves foráneas
    id_categoria = Column(Integer, ForeignKey("categoria.id"))
    id_tipo_producto = Column(Integer, ForeignKey("tipo_producto.id"))
    id_marca = Column(Integer, ForeignKey("marca.id"))
    
    # Relaciones
    categoria = relationship("Categoria", back_populates="productos")
    tipo_producto = relationship("TipoProducto")
    marca = relationship("Marca")
