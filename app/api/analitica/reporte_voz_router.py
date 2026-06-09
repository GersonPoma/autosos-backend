from typing import Any, Literal

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.cuentas.usuario import Usuario
from app.services.analitica import exportar_service, reporte_voz_service

router = APIRouter(
    prefix="/analitica/reporte-voz",
    tags=["Reporte Media Voz"],
    dependencies=[Depends(get_current_user)],
)


class PeticionVoz(BaseModel):
    url_audio: str


class PeticionExportar(BaseModel):
    titulo: str
    transcripcion: str
    datos: dict[str, Any]
    formato: Literal["pdf", "excel"] = "pdf"


@router.post("/taller")
def reporte_taller(
    peticion: PeticionVoz,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return reporte_voz_service.reporte_voz_taller(db, current_user.id, peticion.url_audio)


@router.post("/tenant/{tenant_id}")
def reporte_tenant(
    tenant_id: int,
    peticion: PeticionVoz,
    db: Session = Depends(get_db),
):
    return reporte_voz_service.reporte_voz_tenant(db, tenant_id, peticion.url_audio)


@router.post("/cliente")
def reporte_cliente(
    peticion: PeticionVoz,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return reporte_voz_service.reporte_voz_cliente(db, current_user.id, peticion.url_audio)


@router.post("/exportar")
def exportar_reporte(peticion: PeticionExportar):
    if peticion.formato == "pdf":
        buffer = exportar_service.generar_pdf(peticion.titulo, peticion.transcripcion, peticion.datos)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="reporte.pdf"'},
        )
    buffer = exportar_service.generar_excel(peticion.titulo, peticion.transcripcion, peticion.datos)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="reporte.xlsx"'},
    )