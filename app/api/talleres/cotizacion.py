from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.talleres.cotizacion import CotizacionCrear, CotizacionSalida, AceptarCotizacionSalida
from app.services.talleres import cotizacion_service

router = APIRouter(prefix="/cotizaciones", tags=["Cotizaciones"], dependencies=[Depends(get_current_user)])


@router.post("/", response_model=CotizacionSalida, status_code=status.HTTP_201_CREATED)
def crear(data: CotizacionCrear, db: Session = Depends(get_db)):
    return cotizacion_service.crear(db, data)


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
def aceptar(cotizacion_id: int, db: Session = Depends(get_db)):
    return cotizacion_service.aceptar(db, cotizacion_id)


@router.post("/{cotizacion_id}/rechazar", response_model=CotizacionSalida)
def rechazar(cotizacion_id: int, db: Session = Depends(get_db)):
    return cotizacion_service.rechazar(db, cotizacion_id)