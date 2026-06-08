from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.core.base_model import SoftDelete
from app.db.session import Base


class EstadoIncidente(str, PyEnum):
    PENDIENTE = "Pendiente"
    EN_PROCESO = "En proceso"
    ATENDIDO = "Atendido"
    CANCELADO = "Cancelado"

class PrioridadIncidente(str, PyEnum):
    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"
    INCIERTA = "Incierta"

class Incidente(Base, SoftDelete):
    __tablename__ = "incidente"

    id = Column(Integer, primary_key=True)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    fecha_hora = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    estado = Column(
        Enum(
            EstadoIncidente,
            name="estado_incidente_enum",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
        default=EstadoIncidente.PENDIENTE,
    )
    prioridad = Column(
        Enum(
            PrioridadIncidente,
            name="prioridad_incidente_enum",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
        default=PrioridadIncidente.INCIERTA,
    )
    usuario_id = Column(
        Integer,
        ForeignKey("usuario.id"),
        nullable=False
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=True)

    usuario = relationship("Usuario", backref="incidentes")
    tenant = relationship("Tenant", backref="incidentes")
    analisis = relationship("Analisis", back_populates="incidente", uselist=False)