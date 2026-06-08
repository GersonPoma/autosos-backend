from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.cuentas.usuario import Usuario
from app.models.emergencias.incidente import PrioridadIncidente
from app.models.ia.analisis import Analisis
from app.schemas.emergencias.incidente import IncidenteActualizar
from app.schemas.ia.analisis import AnalisisCrear
from app.services.emergencias import incidente_service
from app.services.ia import analisis_service
from app.services.talleres.service_asignacion import buscar_y_notificar_talleres

router = APIRouter(prefix="/ia", tags=["IA"])


class PeticionProcesarEvidencia(BaseModel):
    id_incidente: int
    url_audio: str
    urls_fotos: list[str]


class DatosProcesadosRespuesta(BaseModel):
    incidente_id: int
    categoria: str
    prioridad_asignada: PrioridadIncidente
    analisis_id: int


class ProcesarEvidenciaRespuesta(BaseModel):
    estado: str
    mensaje: str
    datos_procesados: DatosProcesadosRespuesta


@router.post("/procesar-evidencia", response_model=ProcesarEvidenciaRespuesta)
def procesar_incidente(
    peticion: PeticionProcesarEvidencia,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    incidente_id = peticion.id_incidente

    incidente = incidente_service.obtener_por_id(db, incidente_id)
    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no encontrado")

    analisis_existente = db.query(Analisis).filter(
        Analisis.incidente_id == incidente_id,
        Analisis.deleted == False,
    ).first()
    if analisis_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El incidente ya tiene un analisis asociado",
        )

    if not peticion.url_audio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe enviar una url de audio",
        )
    if not peticion.urls_fotos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe enviar al menos una url de foto",
        )

    try:
        from app.services.ia import ia_service
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo cargar el servicio de IA: {exc}",
        )

    try:
        resultado = ia_service.generar_ficha_servicio(peticion.url_audio, peticion.urls_fotos)
    except ValueError as exc:
        mensaje = str(exc)
        if "|" in mensaje:
            tipo, motivo = mensaje.split("|", 1)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"codigo": tipo, "mensaje": motivo},
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=mensaje)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo completar el analisis con IA",
        )

    ficha = resultado["ficha_para_insertar"]
    analisis_data = AnalisisCrear(
        transcripcion_audio=ficha["transcripcion_audio"],
        categoria_problema=ficha["categoria_problema"],
        danios_identificados=ficha["danios_identificados"],
        resumen_estructurado=ficha["resumen_estructurado"],
        incidente_id=incidente_id,
    )
    analisis = analisis_service.crear(db, analisis_data)

    try:
        prioridad = PrioridadIncidente(resultado["prioridad_para_actualizar"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La IA devolvio una prioridad invalida",
        )

    incidente_actualizado = incidente_service.actualizar(
        db,
        incidente_id,
        IncidenteActualizar(prioridad=prioridad),
    )

    buscar_y_notificar_talleres(
        db=db,
        incidente_id=incidente_actualizado.id,
        incidente_lat=incidente.latitud,
        incidente_lon=incidente.longitud,
        categoria_problema=analisis.categoria_problema,
        prioridad=incidente_actualizado.prioridad.value,
    )

    return {
        "estado": "exito",
        "mensaje": "Evidencia analizada y guardada correctamente.",
        "datos_procesados": {
            "incidente_id": incidente_actualizado.id,
            "categoria": analisis.categoria_problema,
            "prioridad_asignada": incidente_actualizado.prioridad,
            "analisis_id": analisis.id,
        },
    }


