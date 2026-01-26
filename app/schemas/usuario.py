from pydantic import BaseModel
from typing import Optional


# PYDANTIC SCHEMAS SIRVE PARA VALIDAR Y
# ESTRUCTURAR LOS DATOS QUE SE ENVIAN Y RECIBEN A TRAVES DE LA API


# SQLAlchemy decide qué datos existen
# Pydantic decide qué datos se muestran
class TipoUsuarioResponse(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True

class UsuarioBase(BaseModel):
    nombre: str
    apellido: str
    dni: str

# Para crear (POST)
class UsuarioCreate(UsuarioBase):
    password: str
    id_tipo_usuario: int


# Para devolver datos (GET)

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    dni: str
    tipo_usuario: TipoUsuarioResponse

    model_config = {"from_attributes": True}






 