"""
Archivo de entrada de la aplicación FastAPI.
Punto de inicio de la API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import auth, usuarios, categorias, productos, marcas, tiposProducto, clientes, proveedores, compras, ventas, upload, presentaciones
from app.database import engine, Base

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Obtener configuración
settings = get_settings()

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Incluir routers
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(clientes.router)
app.include_router(proveedores.router)
app.include_router(categorias.router)
app.include_router(marcas.router)
app.include_router(tiposProducto.router)
app.include_router(productos.router)
app.include_router(presentaciones.router)
app.include_router(compras.router)
app.include_router(ventas.router)
app.include_router(upload.router, prefix="/api/v1/upload", tags=["Upload"])


@app.get("/")
def root():
    """Endpoint raíz de prueba."""
    return {
        "mensaje": "Bienvenido a la API de Inventario y Ventas",
        "versión": settings.API_VERSION,
        "documentación": "/docs"
    }


@app.get("/health")
def health():
    """Verificar salud de la aplicación."""
    return {"status": "ok"}
