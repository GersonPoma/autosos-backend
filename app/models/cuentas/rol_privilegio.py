from sqlalchemy import Table, Column, Integer, ForeignKey

from app.db.session import Base

rol_privilegio = Table(
    "rol_privilegio",
    Base.metadata,
    Column("rol_id", Integer, ForeignKey("rol.id"), primary_key=True),
    Column("privilegio_id", Integer, ForeignKey("privilegio.id"), primary_key=True),
)