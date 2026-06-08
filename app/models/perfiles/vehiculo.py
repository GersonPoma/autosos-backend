from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.base_model import SoftDelete
from app.db.session import Base


class Vehiculo(Base, SoftDelete):
    __tablename__ = "vehiculo"

    id = Column(Integer, primary_key=True)
    placa = Column(String(20), nullable=False, unique=True)
    modelo = Column(String(100), nullable=False)
    color = Column(String(50), nullable=False)
    cliente_id = Column(Integer, ForeignKey("cliente.id"), nullable=False, unique=True)

    cliente = relationship("Cliente", back_populates="vehiculo")
