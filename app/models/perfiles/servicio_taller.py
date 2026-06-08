from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.core.base_model import SoftDelete
from app.db.session import Base


class ServicioTaller(Base, SoftDelete):
    __tablename__ = "servicio_taller"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), nullable=False)
    categoria = Column(String(150), nullable=False)
    precio = Column(Float, nullable=False)
    taller_id = Column(Integer, ForeignKey("taller.id"), nullable=False)

    taller = relationship("Taller", back_populates="servicios")
    detalles = relationship("DetalleOrden", back_populates="servicio_taller")

    @property
    def taller_nombre(self):
        return self.taller.nombre if self.taller else None
