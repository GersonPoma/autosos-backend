from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, Enum, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.core.base_model import SoftDelete
from app.db.session import Base


class TipoEvidencia(str, PyEnum):
    FOTO = "Foto"
    AUDIO = "Audio"
    TEXTO = "Texto"

class Evidencia(Base, SoftDelete):
    __tablename__ = "evidencia"

    id = Column(Integer, primary_key=True)
    tipo = Column(
        Enum(
            TipoEvidencia,
            name="tipo_evidencia_enum",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    url = Column(String)
    fecha = Column(
        Date,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).date(),
    )
    incidente_id = Column(Integer, ForeignKey("incidente.id"), nullable=False)

    incidente = relationship("Incidente", backref="evidencias")