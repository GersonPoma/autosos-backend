from sqlalchemy.orm import Session

from app.models.perfiles.taller import Taller

SCORE_MIN = 1
SCORE_MAX = 100

PUNTOS_SLA_CUMPLIDO = 5
PUNTOS_CALIFICACION_5_ESTRELLAS = 3


def ajustar_score(db: Session, taller_id: int, delta: int) -> Taller | None:
    """Suma o resta puntos al score de confianza de un taller, acotado entre 1 y 100."""
    taller = db.query(Taller).filter(Taller.id == taller_id).first()
    if not taller:
        return None

    taller.score_confianza = max(SCORE_MIN, min(SCORE_MAX, taller.score_confianza + delta))
    db.commit()
    db.refresh(taller)
    return taller


def evaluar_sla_llegada(db: Session, taller_id: int, segundos_transcurridos: float, segundos_estimados: int) -> None:
    """+5 puntos si el taller llegó dentro (o antes) del tiempo estimado."""
    if segundos_transcurridos <= segundos_estimados:
        ajustar_score(db, taller_id, PUNTOS_SLA_CUMPLIDO)


def evaluar_calificacion(db: Session, taller_id: int, estrellas: float) -> None:
    """+3 puntos si el cliente calificó con 5 estrellas."""
    if estrellas == 5:
        ajustar_score(db, taller_id, PUNTOS_CALIFICACION_5_ESTRELLAS)