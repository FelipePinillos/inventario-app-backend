from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# Schema para Cliente simplificado
class ClienteSimple(BaseModel):
    id: int
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    dni: Optional[str] = None
    
    model_config = {"from_attributes": True}

# Schema para Usuario simplificado
class UsuarioSimple(BaseModel):
    id: int
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    
    model_config = {"from_attributes": True}

# Schema para Producto en detalle (simplificado)
class ProductoSimple(BaseModel):
    id: int
    codigo: str
    nombre: Optional[str] = None
    
    model_config = {"from_attributes": True}

# Schema para Presentacion en detalle (simplificado)
class PresentacionSimple(BaseModel):
    id: int
    nombre: str
    cantidad_base: int
    precio_venta: Decimal
    
    model_config = {"from_attributes": True}

# ============ SCHEMAS PARA DETALLE VENTA ============

class DetalleVentaBase(BaseModel):
    id_presentacion: int
    cantidad: int
    precio_unitario: Decimal = Field(decimal_places=2)
    subtotal: Optional[Decimal] = Field(None, decimal_places=2)
    id_producto: Optional[int] = None  # Campo opcional para compatibilidad con frontend

class DetalleVentaCreate(DetalleVentaBase):
    """Schema para crear un detalle de venta"""
    pass

class DetalleVentaResponse(DetalleVentaBase):
    """Schema para respuesta de detalle de venta con relaciones"""
    id: int
    id_venta: Optional[int] = None
    presentacion: Optional[PresentacionSimple] = None
    producto: Optional[ProductoSimple] = None
    
    model_config = {"from_attributes": True}

# ============ SCHEMAS PARA VENTA ============

class VentaBase(BaseModel):
    id_cliente: Optional[int] = None
    fecha: Optional[datetime] = None
    descuento: Optional[Decimal] = Field(0, decimal_places=2)
    id_usuario: Optional[int] = None
    estado: Optional[str] = "CONFIRMADA"
    # Campos opcionales que puede enviar el frontend (se recalculan automáticamente)
    totalcondescuento: Optional[Decimal] = Field(None, decimal_places=2)
    totalsindescuento: Optional[Decimal] = Field(None, decimal_places=2)
    # fecha_creacion y fecha_edicion removidos para evitar conflictos de validación

class VentaCreate(VentaBase):
    """Schema para crear una venta con sus detalles"""
    detalles: List[DetalleVentaCreate] = Field(default_factory=list)
    
    @field_validator('detalles')
    @classmethod
    def validar_detalles(cls, v):
        if not v or len(v) == 0:
            raise ValueError("La venta debe tener al menos un detalle")
        return v

class VentaUpdate(BaseModel):
    """Schema para actualizar una venta (sin detalles)"""
    id_cliente: Optional[int] = None
    fecha: Optional[datetime] = None
    descuento: Optional[Decimal] = Field(None, decimal_places=2)
    id_usuario: Optional[int] = None
    estado: Optional[str] = None

class VentaResponse(VentaBase):
    """Schema para respuesta de venta con totales calculados"""
    id: int
    totalcondescuento: Optional[Decimal] = None
    totalsindescuento: Optional[Decimal] = None
    cliente: Optional[ClienteSimple] = None
    usuario: Optional[UsuarioSimple] = None
    detalles: List[DetalleVentaResponse] = Field(default_factory=list)
    
    model_config = {"from_attributes": True}
