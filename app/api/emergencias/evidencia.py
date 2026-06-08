from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.cuentas.usuario import Usuario
from app.schemas.emergencias.evidencia import EvidenciaActualizar, EvidenciaCrear, EvidenciaSalida
from app.services.emergencias import evidencia_service

router = APIRouter(prefix="/evidencias", tags=["Evidencias"])


@router.post("/", response_model=EvidenciaSalida, status_code=status.HTTP_201_CREATED)
def crear(
    data: EvidenciaCrear,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return evidencia_service.crear(db, data)


@router.get("/incidente/{incidente_id}", response_model=PaginacionSalida[EvidenciaSalida])
def obtener_por_incidente_id(
    incidente_id: int,
    pagina: int = 1,
    limite: int = 10,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return evidencia_service.obtener_por_incidente_id(db, incidente_id, pagina, limite)


@router.get("/{evidencia_id}", response_model=EvidenciaSalida)
def obtener_por_id(
    evidencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    evidencia = evidencia_service.obtener_por_id(db, evidencia_id)
    if not evidencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidencia no encontrada")
    return evidencia


@router.put("/{evidencia_id}", response_model=EvidenciaSalida)
def actualizar(
    evidencia_id: int,
    data: EvidenciaActualizar,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    evidencia = evidencia_service.actualizar(db, evidencia_id, data)
    if not evidencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidencia no encontrada")
    return evidencia


@router.delete("/{evidencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    evidencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    evidencia = evidencia_service.eliminar(db, evidencia_id)
    if not evidencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidencia no encontrada")


