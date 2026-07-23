from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.cuentas.usuario import Usuario
from app.schemas.emergencias.incidente import IncidenteActualizar, IncidenteCrear, IncidenteSalida
from app.services.analitica import exportar_service
from app.services.emergencias import incidente_service
from app.tracking.manager import manager

router = APIRouter(prefix="/incidentes", tags=["Incidentes"])


@router.post("/", response_model=IncidenteSalida, status_code=status.HTTP_201_CREATED)
def crear(
    data: IncidenteCrear,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return incidente_service.crear(db, data, current_user.id)


@router.get("/usuario/{usuario_id}", response_model=PaginacionSalida[IncidenteSalida])
def obtener_por_usuario_id(
    usuario_id: int,
    pagina: int = 1,
    limite: int = 10,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return incidente_service.obtener_por_usuario_id(db, usuario_id, pagina, limite)


@router.get("/usuario/{usuario_id}/activo", response_model=IncidenteSalida)
def obtener_activo_por_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    incidente = incidente_service.obtener_activo_por_usuario(db, usuario_id)
    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No hay incidente activo para este usuario")
    return incidente


@router.get("/{incidente_id}", response_model=IncidenteSalida)
def obtener_por_id(
    incidente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    incidente = incidente_service.obtener_por_id(db, incidente_id)
    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no encontrado")
    return incidente


@router.get("/{incidente_id}/detalle", response_model=dict)
def obtener_detalle_completo(
    incidente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    detalle = incidente_service.obtener_detalle_incidente(db, incidente_id)
    if not detalle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no encontrado")
    return detalle


@router.get("/{incidente_id}/reporte-siniestro")
def obtener_reporte_siniestro(
    incidente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    incidente = incidente_service.obtener_por_id(db, incidente_id)
    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no encontrado")

    if not incidente_service.usuario_autorizado_incidente(db, incidente, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este incidente")

    datos = incidente_service.obtener_datos_siniestro(db, incidente_id)
    buffer = exportar_service.generar_pdf_siniestro(datos)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="siniestro_{incidente_id}.pdf"'},
    )


@router.put("/{incidente_id}", response_model=IncidenteSalida)
def actualizar(
    incidente_id: int,
    data: IncidenteActualizar,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    incidente = incidente_service.actualizar(db, incidente_id, data)
    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no encontrado")
    return incidente


@router.patch("/{incidente_id}/cancelar", response_model=IncidenteSalida)
async def cancelar_incidente(
    incidente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    incidente = incidente_service.cancelar_incidente(db, incidente_id)
    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no encontrado")
    await manager.broadcast(incidente_id, {
        "evento": "incidente_cancelado",
        "data": {"incidente_id": incidente_id},
    })
    return incidente

