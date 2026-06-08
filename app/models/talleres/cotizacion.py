from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.core.base_model import SoftDelete
from app.db.session import Base


class EstadoCotizacion(str, PyEnum):
    PENDIENTE = "Pendiente"
    ACEPTADA = "Aceptada"
    RECHAZADA = "Rechazada"
    EXPIRADA = "Expirada"


class TipoAtencion(str, PyEnum):
    EN_LUGAR = "En lugar"
    EN_TALLER = "En taller"


class Cotizacion(Base, SoftDelete):
    __tablename__ = "cotizacion"

    id = Column(Integer, primary_key=True)
    estado_cotizacion = Column(
        Enum(EstadoCotizacion, name="estado_cotizacion_enum", native_enum=False, validate_strings=True),
        nullable=False,
        default=EstadoCotizacion.PENDIENTE,
    )
    tipo_atencion = Column(
        Enum(TipoAtencion, name="tipo_atencion_enum", native_enum=False, validate_strings=True),
        nullable=False,
    )
    distancia_km = Column(Float, nullable=False)
    tiempo_estimado_llegada = Column(Integer, nullable=False)
    costo_total = Column(Float, nullable=False, default=0.0)
    fecha_emision = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_validez = Column(DateTime(timezone=True), nullable=False)

    asignacion_candidato_id = Column(Integer, ForeignKey("asignacion_candidato.id"), unique=True, nullable=False)

    asignacion_candidato = relationship("AsignacionCandidato", back_populates="cotizacion")
    detalles = relationship("DetalleCotizacion", back_populates="cotizacion")
    orden_servicio = relationship("OrdenServicio", back_populates="cotizacion", uselist=False)


class DetalleCotizacion(Base, SoftDelete):
    __tablename__ = "detalle_cotizacion"

    id = Column(Integer, primary_key=True)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    cotizacion_id = Column(Integer, ForeignKey("cotizacion.id"), nullable=False)
    servicio_taller_id = Column(Integer, ForeignKey("servicio_taller.id"), nullable=False)

    cotizacion = relationship("Cotizacion", back_populates="detalles")
    servicio_taller = relationship("ServicioTaller", backref="detalles_cotizacion")

    @property
    def servicio_nombre(self):
        return self.servicio_taller.nombre if self.servicio_taller else None