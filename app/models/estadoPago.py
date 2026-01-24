from sqlalchemy import Column, Integer, String
from app.database import Base

class EstadoPago(Base):
    __tablename__ = "estado_pago"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(45), nullable=False)
