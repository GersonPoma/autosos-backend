from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.pagos.detalle_orden import DetalleOrdenEntrada, DetalleOrdenSalida
from app.services.pagos import service_detalle_orden

router = APIRouter(
    prefix="/detalles-orden",
    tags=["Detalles de Orden"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/", response_model=DetalleOrdenSalida, status_code=status.HTTP_201_CREATED)
def crear(entrada: DetalleOrdenEntrada, db: Session = Depends(get_db)):
    return service_detalle_orden.crear(db, entrada)


@router.get("/orden/{orden_id}", response_model=PaginacionSalida[DetalleOrdenSalida])
def listar_por_orden(orden_id: int, pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return service_detalle_orden.obtener_por_orden(db, orden_id, pagina, limite)


@router.get("/{detalle_id}", response_model=DetalleOrdenSalida)
def obtener(detalle_id: int, db: Session = Depends(get_db)):
    detalle = service_detalle_orden.obtener_por_id(db, detalle_id)
    if not detalle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle de orden no encontrado")
    return detalle


@router.delete("/{detalle_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(detalle_id: int, db: Session = Depends(get_db)):
    eliminado = service_detalle_orden.eliminar(db, detalle_id)
    if not eliminado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle de orden no encontrado")
