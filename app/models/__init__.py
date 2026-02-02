# Importar todos los modelos aquí para que SQLAlchemy los encuentre
from .categoria import Categoria
from .cliente import Cliente
from .compra import Compra, DetalleCompra
from .estadoPago import EstadoPago
from .marca import Marca
from .presentacion import Presentacion
from .producto import Producto
from .proveedor import Proveedor
from .tipoProducto import TipoProducto
from .tipoUsuario import TipoUsuario
from .usuario import Usuario
from .venta import Venta

__all__ = [
    'Categoria',
    'Cliente', 
    'Compra',
    'DetalleCompra',
    'EstadoPago',
    'Marca',
    'Presentacion',
    'Producto',
    'Proveedor',
    'TipoProducto',
    'TipoUsuario',
    'Usuario',
    'Venta'
]