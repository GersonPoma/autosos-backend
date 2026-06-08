from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.talleres.asignacion_candidato import (
    AsignacionCandidatoSalida,
    RechazarEmergenciaSalida,
)
from app.services.talleres import service_asignacion

router = APIRouter(
    prefix="/asignaciones",
    tags=["Asignaciones"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/taller/{taller_id}/emergencias-pendientes", response_model=list[AsignacionCandidatoSalida])
def ver_emergencias_pendientes(taller_id: int, db: Session = Depends(get_db)):
    return service_asignacion.obtener_pendientes_por_taller(db, taller_id)


@router.get("/taller/{taller_id}/aceptadas", response_model=PaginacionSalida[AsignacionCandidatoSalida])
def ver_emergencias_aceptadas(taller_id: int, pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return service_asignacion.obtener_aceptadas_por_taller(db, taller_id, pagina, limite)


@router.get("/tenant/{tenant_id}/aceptadas", response_model=PaginacionSalida[AsignacionCandidatoSalida])
def ver_aceptadas_por_tenant(tenant_id: int, pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return service_asignacion.obtener_aceptadas_por_tenant(db, tenant_id, pagina, limite)



@router.post("/asignacion/{asignacion_id}/rechazar", response_model=RechazarEmergenciaSalida)
def rechazar_emergencia(asignacion_id: int, db: Session = Depends(get_db)):
    """Endpoint cuando el mecánico rechaza o ignora una emergencia."""
    return service_asignacion.rechazar_asignacion(db=db, asignacion_id=asignacion_id)
