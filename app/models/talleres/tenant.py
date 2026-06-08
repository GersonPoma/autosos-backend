from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime

from app.core.base_model import SoftDelete
from app.db.session import Base


class Tenant(Base, SoftDelete):
    __tablename__ = "tenant"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)