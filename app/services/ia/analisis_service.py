from sqlalchemy.orm import Session

from app.models.ia.analisis import Analisis
from app.schemas.ia.analisis import AnalisisCrear


def crear(db: Session, data: AnalisisCrear) -> Analisis:
    analisis = Analisis()
    analisis.transcripcion_audio = data.transcripcion_audio
    analisis.categoria_problema = data.categoria_problema
    analisis.danios_identificados = data.danios_identificados
    analisis.resumen_estructurado = data.resumen_estructurado
    analisis.incidente_id = data.incidente_id

    db.add(analisis)
    db.commit()
    db.refresh(analisis)
    return analisis


def obtener_por_incidente_id(db: Session, incidente_id: int):
    return db.query(Analisis).filter(
        Analisis.incidente_id == incidente_id,
        Analisis.deleted == False,
    ).first()
