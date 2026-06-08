from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.core.base_model import SoftDelete
from app.db.session import Base


class Taller(Base, SoftDelete):
    __tablename__ = "taller"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), nullable=False)
    telefono = Column(String(20), nullable=False)
    direccion = Column(String(255), nullable=False)
    disponible = Column(Boolean, nullable=False, default=True)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)

    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False, unique=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=True)

    usuario = relationship("Usuario", backref="taller")
    tenant = relationship("Tenant", backref="talleres")
    servicios = relationship("ServicioTaller", back_populates="taller")
    tecnicos = relationship("Tecnico", back_populates="taller")
