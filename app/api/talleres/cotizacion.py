from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.talleres.cotizacion import CotizacionCrear, CotizacionSalida, AceptarCotizacionSalida
from app.services.talleres import cotizacion_service
from app.tracking.manager import manager

router = APIRouter(prefix="/cotizaciones", tags=["Cotizaciones"], dependencies=[Depends(get_current_user)])


@router.post("/", response_model=CotizacionSalida, status_code=status.HTTP_201_CREATED)
async def crear(data: CotizacionCrear, db: Session = Depends(get_db)):
    cotizacion = cotizacion_service.crear(db, data)
    incidente_id = cotizacion.asignacion_candidato.incidente_id
    await manager.broadcast(incidente_id, {
        "evento": "cotizacion_enviada",
        "data": {
            "cotizacion_id": cotizacion.id,
            "costo_total": cotizacion.costo_total,
            "tiempo_estimado_llegada": cotizacion.tiempo_estimado_llegada,
            "taller_nombre": cotizacion.asignacion_candidato.taller.nombre if cotizacion.asignacion_candidato.taller else None,
        },
    })
    return cotizacion


@router.get("/incidente/{incidente_id}", response_model=list[CotizacionSalida])
def listar_por_incidente(incidente_id: int, db: Session = Depends(get_db)):
    return cotizacion_service.listar_por_incidente(db, incidente_id)


@router.get("/{cotizacion_id}", response_model=CotizacionSalida)
def obtener(cotizacion_id: int, db: Session = Depends(get_db)):
    cotizacion = cotizacion_service.obtener_por_id(db, cotizacion_id)
    if not cotizacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada")
    return cotizacion


@router.post("/{cotizacion_id}/aceptar", response_model=AceptarCotizacionSalida)
async def aceptar(cotizacion_id: int, db: Session = Depends(get_db)):
    cotizacion = cotizacion_service.obtener_por_id(db, cotizacion_id)
    if not cotizacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada")
    incidente_id = cotizacion.asignacion_candidato.incidente_id
    resultado = cotizacion_service.aceptar(db, cotizacion_id)
    await manager.broadcast(incidente_id, {
        "evento": "cotizacion_aceptada",
        "data": resultado,
    })
    return resultado


@router.post("/{cotizacion_id}/rechazar", response_model=CotizacionSalida)
async def rechazar(cotizacion_id: int, db: Session = Depends(get_db)):
    cotizacion = cotizacion_service.rechazar(db, cotizacion_id)
    incidente_id = cotizacion.asignacion_candidato.incidente_id
    await manager.broadcast(incidente_id, {
        "evento": "cotizacion_rechazada",
        "data": {"cotizacion_id": cotizacion_id},
    })
    return cotizacion