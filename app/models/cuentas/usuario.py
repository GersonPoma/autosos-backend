from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from app.core.base_model import SoftDelete
from app.db.session import Base


class Usuario(Base, SoftDelete):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    rol_id = Column(Integer, ForeignKey("rol.id"), nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=True)
    fcm_token = Column(Text, nullable=True)
    super_usuario = Column(Boolean, nullable=False, default=False)

    rol = relationship("Rol", backref="usuarios")
    tenant = relationship("Tenant", backref="usuarios")

    @property
    def rol_nombre(self):
        return self.rol.nombre if self.rol else None
