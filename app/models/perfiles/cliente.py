from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.core.base_model import SoftDelete
from app.db.session import Base


class Cliente(Base, SoftDelete):
    __tablename__ = "cliente"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    fecha_nacimiento = Column(Date, nullable=True)
    email = Column(String(150), nullable=True)
    telefono = Column(String(20), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False, unique=True)

    usuario = relationship("Usuario", backref="cliente")
    vehiculo = relationship("Vehiculo", back_populates="cliente", uselist=False)
