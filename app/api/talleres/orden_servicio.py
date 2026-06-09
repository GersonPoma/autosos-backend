from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.talleres.orden_servicio import EstadoOperacion
from app.schemas.talleres.orden_servicio import OrdenServicioSalida, OrdenServicioLista, OrdenServicioCalificar
from app.services.talleres import service_orden_servicio
from app.tracking.manager import manager

router = APIRouter(prefix="/ordenes-servicio", tags=["Ordenes Servicio"], dependencies=[Depends(get_current_user)])


class CambiarEstadoEntrada(BaseModel):
    estado: EstadoOperacion


@router.get("/", response_model=PaginacionSalida[OrdenServicioSalida])
def listar(pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return service_orden_servicio.obtener_todos(db, pagina, limite)


@router.get("/taller/{taller_id}", response_model=PaginacionSalida[OrdenServicioLista])
def listar_por_taller(taller_id: int, pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return service_orden_servicio.obtener_por_taller_id(db, taller_id, pagina, limite)


@router.get("/tenant/{tenant_id}", response_model=PaginacionSalida[OrdenServicioLista])
def listar_por_tenant(tenant_id: int, pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return service_orden_servicio.obtener_por_tenant_id(db, tenant_id, pagina, limite)


@router.get("/incidente/{incidente_id}", response_model=OrdenServicioSalida)
def obtener_por_incidente(incidente_id: int, db: Session = Depends(get_db)):
    orden = service_orden_servicio.obtener_por_incidente_id(db, incidente_id)
    if not orden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden de servicio no encontrada")
    return orden


@router.patch("/{orden_id}/estado", response_model=OrdenServicioSalida)
async def cambiar_estado(orden_id: int, data: CambiarEstadoEntrada, db: Session = Depends(get_db)):
    orden = service_orden_servicio.cambiar_estado(db, orden_id, data.estado)
    if not orden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden de servicio no encontrada")
    await manager.broadcast(orden["incidente_id"], {
        "evento": "estado_orden_cambiado",
        "data": {"orden_id": orden_id, "estado": data.estado.value},
    })
    return orden


@router.patch("/{orden_id}/calificar", response_model=OrdenServicioSalida)
def calificar(orden_id: int, data: OrdenServicioCalificar, db: Session = Depends(get_db)):
    orden = service_orden_servicio.calificar(db, orden_id, data.estrellas, data.comentario)
    if not orden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden de servicio no encontrada")
    return orden


@router.get("/{orden_id}", response_model=OrdenServicioSalida)
def obtener_por_id(orden_id: int, db: Session = Depends(get_db)):
    orden = service_orden_servicio.obtener_por_id(db, orden_id)
    if not orden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden de servicio no encontrada")
    return orden