from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.base_model import SoftDelete
from app.db.session import Base
from app.models.cuentas.rol_privilegio import rol_privilegio


class Rol(Base, SoftDelete):
    __tablename__ = "rol"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=True)

    privilegios = relationship("Privilegio", secondary=rol_privilegio)
    tenant = relationship("Tenant", backref="roles")