from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.cuentas.usuario import Usuario
from app.schemas.ia.analisis import AnalisisSalida
from app.services.ia import analisis_service

router = APIRouter(prefix="/ia/analisis", tags=["IA"])


@router.get("/incidente/{incidente_id}", response_model=AnalisisSalida)
def obtener_por_incidente_id(
    incidente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    analisis = analisis_service.obtener_por_incidente_id(db, incidente_id)
    if not analisis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analisis no encontrado")
    return analisis

