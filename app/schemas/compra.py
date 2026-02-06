from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

# Schema para EstadoPago
class EstadoPagoBase(BaseModel):
    nombre: str

class EstadoPagoResponse(EstadoPagoBase):
    id: int
    
    class Config:
        from_attributes = True

# Schema para Proveedor simplificado
class ProveedorSimple(BaseModel):
    id: int
    razon_social: Optional[str]
    ruc: int
    
    class Config:
        from_attributes = True

# Schema para Usuario simplificado
class UsuarioSimple(BaseModel):
    id: int
    nombre: Optional[str]
    apellido: Optional[str]
    
    class Config:
        from_attributes = True

# Schema para Producto simplificado
class ProductoSimple(BaseModel):
    id: int
    codigo: str
    nombre: Optional[str]
    unidad_base: Optional[str]
    
    class Config:
        from_attributes = True

# Schema para Presentacion simplificado
class PresentacionSimple(BaseModel):
    id: int
    nombre: Optional[str]
    cantidad_base: Optional[int]
    precio_venta: Optional[float]
    precio_compra: Optional[float]
    producto: Optional[ProductoSimple] = None
    
    class Config:
        from_attributes = True

# Schemas para DetalleCompra
class DetalleCompraCreate(BaseModel):
    id_presentacion: int
    cantidad: int
    precio_compra: Optional[Decimal] = Field(None, decimal_places=2, alias='precio_unitario')  # Acepta precio_compra pero lo mapea a precio_unitario
    subtotal: Optional[Decimal] = Field(None, decimal_places=2)  # Opcional, se calcula automáticamente
    
    class Config:
        populate_by_name = True  # Permite usar tanto precio_compra como precio_unitario

class DetalleCompraUpdate(BaseModel):
    id_presentacion: Optional[int] = None
    cantidad: Optional[int] = None
    precio_compra: Optional[Decimal] = Field(None, decimal_places=2, alias='precio_unitario')
    subtotal: Optional[Decimal] = Field(None, decimal_places=2)
    
    class Config:
        populate_by_name = True

class DetalleCompraResponse(BaseModel):
    id: int
    id_compra: int
    id_presentacion: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime]
    presentacion: Optional[PresentacionSimple] = None
    
    class Config:
        from_attributes = True

# Schemas para Compra
class CompraCreate(BaseModel):
    fecha_compra: Optional[datetime] = None
    fecha_entrega: Optional[datetime] = None
    totalcondescuento: Optional[Decimal] = Field(None, decimal_places=2)
    descuento: Decimal = Field(default=0.00, decimal_places=2)
    totalsindescuento: Decimal = Field(..., decimal_places=2)
    id_usuario: Optional[int] = None
    id_proveedor: Optional[int] = None
    estado: str = "CONFIRMADA"
    detalles: Optional[List[DetalleCompraCreate]] = []
    
    
class CompraUpdate(BaseModel):
    fecha_compra: Optional[datetime] = None
    fecha_entrega: Optional[datetime] = None
    totalcondescuento: Optional[Decimal] = Field(None, decimal_places=2)
    descuento: Optional[Decimal] = Field(None, decimal_places=2)
    totalsindescuento: Optional[Decimal] = Field(None, decimal_places=2)
    id_usuario: Optional[int] = None
    id_proveedor: Optional[int] = None
    estado: Optional[str] = None


class CompraResponse(BaseModel):
    id: int
    fecha_compra: Optional[datetime]
    fecha_entrega: Optional[datetime]
    totalcondescuento: Optional[Decimal]
    descuento: Decimal
    totalsindescuento: Decimal
    id_usuario: Optional[int]
    id_proveedor: Optional[int]
    estado: str
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime]
    usuario: Optional[UsuarioSimple] = None
    proveedor: Optional[ProveedorSimple] = None
    detalles: Optional[List[DetalleCompraResponse]] = []
    
    class Config:
        from_attributes = True
