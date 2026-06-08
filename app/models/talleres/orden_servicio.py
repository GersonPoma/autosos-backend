from datetime import timezone, datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey, Float, Text
from sqlalchemy.orm import relationship

from app.core.base_model import SoftDelete
from app.db.session import Base

class EstadoOperacion(str, PyEnum):
    EN_CAMINO = "En camino"
    DIAGNOSTICANDO = "Diagnosticando"
    REPARANDO = "Reparando"
    FINALIZADO = "Finalizado"

class OrdenServicio(Base, SoftDelete):
    __tablename__ = "orden_servicio"

    id = Column(Integer, primary_key=True)
    fecha_hora = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    tiempo_estimado_llegada = Column(Integer, nullable=False, default=0)
    fecha_hora_llegada = Column(DateTime(timezone=True), nullable=True)
    fecha_hora_fin = Column(DateTime(timezone=True), nullable=True)
    estado = Column(
        Enum(
            EstadoOperacion,
            name="estado_operacion_enum",
            native_enum=False,
            validate_strings=True
        ),
        default=EstadoOperacion.EN_CAMINO,
        nullable=False,
    )

    estrellas = Column(
        Float,
        nullable=True,
    )

    comentario = Column(
        Text,
        nullable=True,
    )

    cotizacion_id = Column(Integer, ForeignKey("cotizacion.id"), unique=True, nullable=False)

    cotizacion = relationship("Cotizacion", back_populates="orden_servicio")
    transaccion = relationship("Transaccion", back_populates="orden_servicio", uselist=False)
    detalles = relationship("DetalleOrden", back_populates="orden_servicio")
