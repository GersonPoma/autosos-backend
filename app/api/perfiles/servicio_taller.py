from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.perfiles.servicio_taller import ServicioTallerCrear, ServicioTallerActualizar, ServicioTallerSalida
from app.services.perfiles import servicio_taller_service

router = APIRouter(prefix="/servicios-taller", tags=["Servicios Taller"], dependencies=[Depends(get_current_user)])


@router.get("/taller/{taller_id}", response_model=PaginacionSalida[ServicioTallerSalida])
def listar_por_taller(taller_id: int, pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return servicio_taller_service.obtener_por_taller(db, taller_id, pagina, limite)


@router.get("/tenant/{tenant_id}", response_model=PaginacionSalida[ServicioTallerSalida])
def listar_por_tenant(tenant_id: int, pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return servicio_taller_service.obtener_por_tenant(db, tenant_id, pagina, limite)


@router.post("/", response_model=ServicioTallerSalida, status_code=status.HTTP_201_CREATED)
def crear(data: ServicioTallerCrear, db: Session = Depends(get_db)):
    return servicio_taller_service.crear(db, data)


@router.put("/{servicio_id}", response_model=ServicioTallerSalida)
def actualizar(servicio_id: int, data: ServicioTallerActualizar, db: Session = Depends(get_db)):
    servicio = servicio_taller_service.actualizar(db, servicio_id, data)
    if not servicio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado")
    return servicio


@router.delete("/{servicio_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(servicio_id: int, db: Session = Depends(get_db)):
    servicio = servicio_taller_service.eliminar(db, servicio_id)
    if not servicio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado")