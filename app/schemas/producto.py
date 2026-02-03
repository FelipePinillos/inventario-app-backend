from pydantic import BaseModel, computed_field
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.presentacion import PresentacionResponse

from app.schemas.categoria import CategoriaResponse
from app.schemas.marca import MarcaResponse
from app.schemas.tipoProducto import TipoProductoResponse


class ProductoBase(BaseModel):
    codigo: str
    nombre: str
    unidad_base: Optional[str] = 'unidad'
    adicional: Optional[str] = None
    stock_minimo: int
    stock_actual: int
    stock_maximo: Optional[int] = None
    avatar: Optional[str] = None
    id_categoria: int
    id_tipo_producto: int
    id_marca: int


class ProductoCreate(ProductoBase):
    """Schema para crear producto."""
    pass


class ProductoUpdate(BaseModel):
    """Schema para actualizar producto."""
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    unidad_base: Optional[str] = None
    adicional: Optional[str] = None
    stock_minimo: Optional[int] = None
    stock_actual: Optional[int] = None
    stock_maximo: Optional[int] = None
    avatar: Optional[str] = None
    id_categoria: Optional[int] = None
    id_tipo_producto: Optional[int] = None
    id_marca: Optional[int] = None


class PresentacionSimple(BaseModel):
    """Schema simple de presentación para evitar importación circular."""
    id: int
    nombre: str
    cantidad_base: int
    precio_venta: float
    precio_compra: float
    estado: str
    
    class Config:
        from_attributes = True


class ProductoResponse(ProductoBase):
    """Schema para respuesta de producto."""
    id: int
    categoria: Optional[CategoriaResponse] = None
    marca: Optional[MarcaResponse] = None
    tipo_producto: Optional[TipoProductoResponse] = None
    presentaciones: Optional[List[PresentacionSimple]] = None  # Para cargar presentaciones
    
    @computed_field
    @property
    def stock_por_presentacion(self) -> List[Dict[str, Any]]:
        """
        Calcula cuántas unidades de cada presentación se pueden formar
        con el stock_actual disponible (de forma independiente).
        
        Ejemplo: Si tienes 230 unidades:
        - Caja x50: 4 cajas (230 / 50 = 4)
        - Pack x25: 9 packs (230 / 25 = 9)
        - Unidad: 230 unidades (230 / 1 = 230)
        """
        if not self.presentaciones:
            return []
        
        distribucion = []
        
        for presentacion in self.presentaciones:
            # Calcular cuántas de esta presentación puedes formar
            cantidad_disponible = self.stock_actual // presentacion.cantidad_base
            unidades_en_presentacion = cantidad_disponible * presentacion.cantidad_base
            unidades_sobrantes = self.stock_actual % presentacion.cantidad_base
            
            distribucion.append({
                "presentacion_id": presentacion.id,
                "nombre": presentacion.nombre,
                "cantidad_base": presentacion.cantidad_base,
                "cantidad_disponible": cantidad_disponible,  # Cuántas de esta presentación
                "unidades_totales": unidades_en_presentacion,  # Unidades en esas presentaciones
                "unidades_sobrantes": unidades_sobrantes,  # Unidades que no completan otra presentación
                "precio_venta": presentacion.precio_venta,
                "precio_compra": presentacion.precio_compra
            })
        
        # Ordenar por cantidad_base de mayor a menor
        distribucion.sort(key=lambda x: x["cantidad_base"], reverse=True)
        
        return distribucion

    class Config:
        from_attributes = True


