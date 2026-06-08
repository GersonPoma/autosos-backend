import math

from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.models.cuentas.privilegio import Privilegio
from app.models.cuentas.rol_privilegio import rol_privilegio
from app.schemas.cuentas.privilegio import PrivilegioActualizar


def obtener_todos(db: Session, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    total = db.query(Privilegio).filter(Privilegio.deleted == False).count()
    datos = db.query(Privilegio).filter(Privilegio.deleted == False).offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=datos,
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def obtener_por_id(db: Session, privilegio_id: int) -> Privilegio | None:
    return db.query(Privilegio).filter(Privilegio.id == privilegio_id, Privilegio.deleted == False).first()


def actualizar(db: Session, privilegio_id: int, data: PrivilegioActualizar) -> Privilegio | None:
    from datetime import datetime
    privilegio = obtener_por_id(db, privilegio_id)
    if not privilegio:
        return None
    if data.nombre is not None:
        privilegio.nombre = data.nombre
    if data.descripcion is not None:
        privilegio.descripcion = data.descripcion
    privilegio.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(privilegio)
    return privilegio


def asignar_a_rol(db: Session, rol_id: int, privilegio_id: int) -> bool:
    existe = db.execute(
        rol_privilegio.select().where(
            rol_privilegio.c.rol_id == rol_id,
            rol_privilegio.c.privilegio_id == privilegio_id,
        )
    ).first()
    if existe:
        return False
    db.execute(rol_privilegio.insert().values(rol_id=rol_id, privilegio_id=privilegio_id))
    db.commit()
    return True


def remover_de_rol(db: Session, rol_id: int, privilegio_id: int) -> bool:
    resultado = db.execute(
        rol_privilegio.delete().where(
            rol_privilegio.c.rol_id == rol_id,
            rol_privilegio.c.privilegio_id == privilegio_id,
        )
    )
    db.commit()
    return resultado.rowcount > 0


def obtener_por_rol(db: Session, rol_id: int) -> list[Privilegio]:
    return db.query(Privilegio).join(
        rol_privilegio, Privilegio.id == rol_privilegio.c.privilegio_id
    ).filter(
        rol_privilegio.c.rol_id == rol_id,
        Privilegio.deleted == False,
    ).all()