from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.base_model import SoftDelete
from app.db.session import Base


class Analisis(Base, SoftDelete):
    __tablename__ = "analisis"

    id = Column(Integer, primary_key=True)
    transcripcion_audio = Column(String, nullable=False)
    categoria_problema = Column(String, nullable=False)
    danios_identificados = Column(String, nullable=False)
    resumen_estructurado = Column(String, nullable=False)

    incidente_id = Column(
        Integer,
        ForeignKey("incidente.id"),
        unique=True,
        nullable=False
    )

    incidente = relationship("Incidente", back_populates="analisis")
