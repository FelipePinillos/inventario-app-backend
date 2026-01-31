from pydantic import BaseModel, field_validator
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

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v

# Para actualizar (PUT)
class UsuarioUpdate(UsuarioBase):
    password: Optional[str] = None
    id_tipo_usuario: int

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v


# Para devolver datos (GET)

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    dni: str
    tipo_usuario: TipoUsuarioResponse

    model_config = {"from_attributes": True}






 