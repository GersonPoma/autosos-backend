from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.core.base_model import SoftDelete
from app.db.session import Base


class DetalleOrden(Base, SoftDelete):
    __tablename__ = "detalle_orden"

    id = Column(Integer, primary_key=True)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    orden_servicio_id = Column(Integer, ForeignKey("orden_servicio.id"), nullable=False)
    servicio_taller_id = Column(Integer, ForeignKey("servicio_taller.id"), nullable=False)

    orden_servicio = relationship("OrdenServicio", back_populates="detalles")
    servicio_taller = relationship("ServicioTaller", back_populates="detalles")

    @property
    def servicio_nombre(self):
        return self.servicio_taller.nombre if self.servicio_taller else None
