from sqlalchemy import Column, Integer, String

from app.core.base_model import SoftDelete
from app.db.session import Base


class Privilegio(Base, SoftDelete):
    __tablename__ = "privilegio"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)