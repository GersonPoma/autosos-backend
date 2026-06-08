from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.core.base_model import SoftDelete
from app.db.session import Base


class EstadoTransaccion(str, PyEnum):
    PENDIENTE = "Pendiente"
    PAGADO = "Pagado"
    CANCELADO = "Cancelado"


class MetodoPago(str, PyEnum):
    EFECTIVO = "Efectivo"
    TARJETA = "Tarjeta"
    TRANSFERENCIA = "Transferencia"


class Transaccion(Base, SoftDelete):
    __tablename__ = "transaccion"

    id = Column(Integer, primary_key=True)
    monto_cobrado = Column(Float, nullable=False)
    monto_comision = Column(Float, nullable=False, default=0.0)
    estado = Column(
        Enum(
            EstadoTransaccion,
            name="estado_transaccion_enum",
            native_enum=False,
            validate_strings=True,
        ),
        default=EstadoTransaccion.PENDIENTE,
        nullable=False,
    )
    metodo_pago = Column(
        Enum(
            MetodoPago,
            name="metodo_pago_enum",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=True,
    )
    fecha_hora = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    orden_servicio_id = Column(
        Integer,
        ForeignKey("orden_servicio.id"),
        unique=True,
        nullable=False,
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=True)

    orden_servicio = relationship("OrdenServicio", back_populates="transaccion")
    tenant = relationship("Tenant", backref="transacciones")

    @property
    def taller_nombre(self):
        try:
            return self.orden_servicio.cotizacion.asignacion_candidato.taller.nombre
        except AttributeError:
            return None
