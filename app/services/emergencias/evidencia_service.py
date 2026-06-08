import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.models.emergencias.evidencia import Evidencia
from app.schemas.emergencias.evidencia import EvidenciaActualizar, EvidenciaCrear


def crear(db: Session, data: EvidenciaCrear) -> Evidencia:
    evidencia = Evidencia()
    evidencia.tipo = data.tipo
    evidencia.url = data.url
    evidencia.incidente_id = data.incidente_id
    db.add(evidencia)
    db.commit()
    db.refresh(evidencia)
    return evidencia


def obtener_por_id(db: Session, evidencia_id: int):
    return db.query(Evidencia).filter(
        Evidencia.id == evidencia_id,
        Evidencia.deleted == False,
    ).first()


def obtener_por_incidente_id(db: Session, incidente_id: int, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    query = db.query(Evidencia).filter(
        Evidencia.incidente_id == incidente_id,
        Evidencia.deleted == False,
    )
    total = query.count()
    datos = query.offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=datos,
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def actualizar(db: Session, evidencia_id: int, data: EvidenciaActualizar):
    evidencia = obtener_por_id(db, evidencia_id)
    if not evidencia:
        return None

    if data.tipo is not None:
        evidencia.tipo = data.tipo
    if data.url is not None:
        evidencia.url = data.url
    if data.fecha is not None:
        evidencia.fecha = data.fecha
    if data.incidente_id is not None:
        evidencia.incidente_id = data.incidente_id

    evidencia.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(evidencia)
    return evidencia


def eliminar(db: Session, evidencia_id: int):
    evidencia = obtener_por_id(db, evidencia_id)
    if not evidencia:
        return None

    db.delete(evidencia)
    db.commit()
    return evidencia


