from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.base_model import SoftDelete
from app.db.session import Base


class Tecnico(Base, SoftDelete):
    __tablename__ = "tecnico"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=False)
    taller_id = Column(Integer, ForeignKey("taller.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False, unique=True)

    taller = relationship("Taller", back_populates="tecnicos")
    usuario = relationship("Usuario", backref="tecnico")

    @property
    def taller_nombre(self):
        return self.taller.nombre if self.taller else None
