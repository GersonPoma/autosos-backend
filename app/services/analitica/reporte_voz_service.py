import json
import os
from datetime import datetime, timezone

import google.generativeai as genai
import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.emergencias.incidente import Incidente, EstadoIncidente
from app.models.pagos.transaccion import Transaccion, EstadoTransaccion
from app.models.perfiles.cliente import Cliente
from app.models.perfiles.taller import Taller
from app.models.talleres.asignacion_candidato import AsignacionCandidato
from app.models.talleres.cotizacion import Cotizacion
from app.models.talleres.orden_servicio import OrdenServicio, EstadoOperacion
from app.models.talleres.tenant import Tenant

load_dotenv()
_API_KEY = os.getenv("GEMINI_API_KEY_VOZ")
if _API_KEY:
    genai.configure(api_key=_API_KEY)

METRICAS_TALLER = [
    "ordenes_activas",
    "ordenes_completadas",
    "promedio_estrellas",
    "ingresos_mes",
    "ingresos_totales",
]

METRICAS_TENANT = [
    "total_talleres",
    "total_incidentes",
    "incidentes_mes",
    "incidentes_activos",
    "ingresos_mes",
    "ingresos_totales",
    "taller_top",
]

METRICAS_CLIENTE = [
    "total_incidentes",
    "incidentes_activos",
    "ultimo_incidente",
    "total_gastado",
    "vehiculo",
]


# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------

def _audio_a_mp3(url_audio: str) -> bytes:
    url_mp3 = (url_audio.rsplit(".", 1)[0] + ".mp3") if "." in url_audio.split("/")[-1] else url_audio + ".mp3"
    try:
        resp = requests.get(url_mp3, timeout=15)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="No se pudo descargar el audio.")
        return resp.content
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=400, detail="El audio tardó demasiado en procesarse.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al descargar el audio: {e}")


def analizar_consulta_voz(url_audio: str, metricas_disponibles: list[str]) -> dict:
    """Transcribe el audio e identifica qué métricas solicitó el usuario."""
    if not _API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada.")

    lista = "\n".join(f"- {m}" for m in metricas_disponibles)
    prompt = f"""Eres un asistente de reportes para un sistema de emergencias vehiculares.
Escucha el audio y determina qué métricas está solicitando el usuario.

Métricas disponibles:
{lista}

Devuelve estrictamente un JSON con esta estructura:
{{
  "transcripcion": "texto exacto del audio",
  "metricas_solicitadas": ["lista", "de", "metricas"],
  "solicita_todo": true o false
}}

Si el usuario pide un resumen general o todas las métricas, pon solicita_todo en true y metricas_solicitadas con todas las métricas disponibles.
Solo incluye métricas de la lista proporcionada."""

    audio_bytes = _audio_a_mp3(url_audio)
    model = genai.GenerativeModel("gemini-2.5-flash")
    try:
        respuesta = model.generate_content(
            [prompt, {"mime_type": "audio/mp3", "data": audio_bytes}],
            generation_config=genai.GenerationConfig(response_mime_type="application/json"),
        )
        resultado = json.loads(respuesta.text)
        if resultado.get("solicita_todo"):
            resultado["metricas_solicitadas"] = metricas_disponibles
        resultado["metricas_solicitadas"] = [
            m for m in resultado.get("metricas_solicitadas", []) if m in metricas_disponibles
        ]
        if not resultado["metricas_solicitadas"]:
            resultado["metricas_solicitadas"] = metricas_disponibles
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error en IA al procesar el audio: {e}")


# ---------------------------------------------------------------------------
# Taller — cálculo de métricas individuales
# ---------------------------------------------------------------------------

def _primer_dia_mes() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _base_ordenes_taller(db: Session, taller_id: int):
    return (
        db.query(OrdenServicio)
        .join(Cotizacion, Cotizacion.id == OrdenServicio.cotizacion_id)
        .join(AsignacionCandidato, AsignacionCandidato.id == Cotizacion.asignacion_candidato_id)
        .filter(
            AsignacionCandidato.taller_id == taller_id,
            OrdenServicio.deleted == False,
            AsignacionCandidato.deleted == False,
            Cotizacion.deleted == False,
        )
    )


def _calc_ordenes_activas(db: Session, taller_id: int) -> int:
    return _base_ordenes_taller(db, taller_id).filter(
        OrdenServicio.estado.in_([
            EstadoOperacion.EN_CAMINO,
            EstadoOperacion.DIAGNOSTICANDO,
            EstadoOperacion.REPARANDO,
        ])
    ).count()


def _calc_ordenes_completadas(db: Session, taller_id: int) -> int:
    return _base_ordenes_taller(db, taller_id).filter(
        OrdenServicio.estado == EstadoOperacion.FINALIZADO
    ).count()


def _calc_promedio_estrellas(db: Session, taller_id: int):
    val = (
        db.query(func.avg(OrdenServicio.estrellas))
        .join(Cotizacion, Cotizacion.id == OrdenServicio.cotizacion_id)
        .join(AsignacionCandidato, AsignacionCandidato.id == Cotizacion.asignacion_candidato_id)
        .filter(
            AsignacionCandidato.taller_id == taller_id,
            OrdenServicio.estrellas.isnot(None),
            OrdenServicio.deleted == False,
        )
        .scalar()
    )
    return round(float(val), 2) if val else None


def _base_transacciones_taller(db: Session, taller_id: int):
    return (
        db.query(Transaccion)
        .join(OrdenServicio, OrdenServicio.id == Transaccion.orden_servicio_id)
        .join(Cotizacion, Cotizacion.id == OrdenServicio.cotizacion_id)
        .join(AsignacionCandidato, AsignacionCandidato.id == Cotizacion.asignacion_candidato_id)
        .filter(
            AsignacionCandidato.taller_id == taller_id,
            Transaccion.estado == EstadoTransaccion.PAGADO,
            Transaccion.deleted == False,
        )
    )


def _calc_ingresos_mes_taller(db: Session, taller_id: int) -> float:
    val = _base_transacciones_taller(db, taller_id).filter(
        Transaccion.fecha_hora >= _primer_dia_mes()
    ).with_entities(func.sum(Transaccion.monto_cobrado)).scalar()
    return round(float(val), 2) if val else 0.0


def _calc_ingresos_totales_taller(db: Session, taller_id: int) -> float:
    val = _base_transacciones_taller(db, taller_id).with_entities(func.sum(Transaccion.monto_cobrado)).scalar()
    return round(float(val), 2) if val else 0.0


_DISPATCH_TALLER = {
    "ordenes_activas": _calc_ordenes_activas,
    "ordenes_completadas": _calc_ordenes_completadas,
    "promedio_estrellas": _calc_promedio_estrellas,
    "ingresos_mes": _calc_ingresos_mes_taller,
    "ingresos_totales": _calc_ingresos_totales_taller,
}


def reporte_voz_taller(db: Session, usuario_id: int, url_audio: str) -> dict:
    taller = db.query(Taller).filter(Taller.usuario_id == usuario_id, Taller.deleted == False).first()
    if not taller:
        raise HTTPException(status_code=404, detail="No tienes un taller registrado.")

    analisis = analizar_consulta_voz(url_audio, METRICAS_TALLER)
    datos = {m: _DISPATCH_TALLER[m](db, taller.id) for m in analisis["metricas_solicitadas"]}

    return {"transcripcion": analisis["transcripcion"], "datos": datos}


# ---------------------------------------------------------------------------
# Tenant — cálculo de métricas individuales
# ---------------------------------------------------------------------------

def _calc_total_talleres(db: Session, tenant_id: int) -> int:
    return db.query(func.count(Taller.id)).filter(Taller.tenant_id == tenant_id, Taller.deleted == False).scalar() or 0


def _calc_total_incidentes(db: Session, tenant_id: int) -> int:
    return db.query(func.count(Incidente.id)).filter(Incidente.tenant_id == tenant_id, Incidente.deleted == False).scalar() or 0


def _calc_incidentes_mes(db: Session, tenant_id: int) -> int:
    return (
        db.query(func.count(Incidente.id))
        .filter(
            Incidente.tenant_id == tenant_id,
            Incidente.fecha_hora >= _primer_dia_mes(),
            Incidente.deleted == False,
        )
        .scalar() or 0
    )


def _calc_incidentes_activos(db: Session, tenant_id: int) -> int:
    return (
        db.query(func.count(Incidente.id))
        .filter(
            Incidente.tenant_id == tenant_id,
            Incidente.estado == EstadoIncidente.EN_PROCESO,
            Incidente.deleted == False,
        )
        .scalar() or 0
    )


def _calc_ingresos_mes_tenant(db: Session, tenant_id: int) -> float:
    val = (
        db.query(func.sum(Transaccion.monto_cobrado))
        .filter(
            Transaccion.tenant_id == tenant_id,
            Transaccion.estado == EstadoTransaccion.PAGADO,
            Transaccion.fecha_hora >= _primer_dia_mes(),
            Transaccion.deleted == False,
        )
        .scalar()
    )
    return round(float(val), 2) if val else 0.0


def _calc_ingresos_totales_tenant(db: Session, tenant_id: int) -> float:
    val = (
        db.query(func.sum(Transaccion.monto_cobrado))
        .filter(
            Transaccion.tenant_id == tenant_id,
            Transaccion.estado == EstadoTransaccion.PAGADO,
            Transaccion.deleted == False,
        )
        .scalar()
    )
    return round(float(val), 2) if val else 0.0


def _calc_taller_top(db: Session, tenant_id: int):
    row = (
        db.query(Taller.nombre, func.count(OrdenServicio.id).label("c"))
        .join(AsignacionCandidato, AsignacionCandidato.taller_id == Taller.id)
        .join(Cotizacion, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .join(OrdenServicio, OrdenServicio.cotizacion_id == Cotizacion.id)
        .filter(
            Taller.tenant_id == tenant_id,
            OrdenServicio.estado == EstadoOperacion.FINALIZADO,
            Taller.deleted == False,
            OrdenServicio.deleted == False,
        )
        .group_by(Taller.nombre)
        .order_by(func.count(OrdenServicio.id).desc())
        .first()
    )
    return row.nombre if row else None


_DISPATCH_TENANT = {
    "total_talleres": _calc_total_talleres,
    "total_incidentes": _calc_total_incidentes,
    "incidentes_mes": _calc_incidentes_mes,
    "incidentes_activos": _calc_incidentes_activos,
    "ingresos_mes": _calc_ingresos_mes_tenant,
    "ingresos_totales": _calc_ingresos_totales_tenant,
    "taller_top": _calc_taller_top,
}


def reporte_voz_tenant(db: Session, tenant_id: int, url_audio: str) -> dict:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.deleted == False).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado.")

    analisis = analizar_consulta_voz(url_audio, METRICAS_TENANT)
    datos = {m: _DISPATCH_TENANT[m](db, tenant_id) for m in analisis["metricas_solicitadas"]}

    return {"transcripcion": analisis["transcripcion"], "datos": datos}


# ---------------------------------------------------------------------------
# Cliente — cálculo de métricas individuales
# ---------------------------------------------------------------------------

def _calc_total_incidentes_cliente(db: Session, usuario_id: int) -> int:
    return (
        db.query(func.count(Incidente.id))
        .filter(Incidente.usuario_id == usuario_id, Incidente.deleted == False)
        .scalar() or 0
    )


def _calc_incidentes_activos_cliente(db: Session, usuario_id: int) -> int:
    return (
        db.query(func.count(Incidente.id))
        .filter(
            Incidente.usuario_id == usuario_id,
            Incidente.estado == EstadoIncidente.EN_PROCESO,
            Incidente.deleted == False,
        )
        .scalar() or 0
    )


def _calc_ultimo_incidente(db: Session, usuario_id: int):
    inc = (
        db.query(Incidente)
        .filter(Incidente.usuario_id == usuario_id, Incidente.deleted == False)
        .order_by(Incidente.fecha_hora.desc())
        .first()
    )
    if not inc:
        return None
    return {"fecha": inc.fecha_hora.isoformat(), "estado": inc.estado.value}


def _calc_total_gastado(db: Session, usuario_id: int) -> float:
    val = (
        db.query(func.sum(Transaccion.monto_cobrado))
        .join(OrdenServicio, OrdenServicio.id == Transaccion.orden_servicio_id)
        .join(Cotizacion, Cotizacion.id == OrdenServicio.cotizacion_id)
        .join(AsignacionCandidato, AsignacionCandidato.id == Cotizacion.asignacion_candidato_id)
        .join(Incidente, Incidente.id == AsignacionCandidato.incidente_id)
        .filter(
            Incidente.usuario_id == usuario_id,
            Transaccion.estado == EstadoTransaccion.PAGADO,
            Transaccion.deleted == False,
        )
        .scalar()
    )
    return round(float(val), 2) if val else 0.0


def _calc_vehiculo(db: Session, usuario_id: int):
    cliente = db.query(Cliente).filter(Cliente.usuario_id == usuario_id, Cliente.deleted == False).first()
    if not cliente or not cliente.vehiculo:
        return None
    return {"placa": cliente.vehiculo.placa, "modelo": cliente.vehiculo.modelo}


_DISPATCH_CLIENTE = {
    "total_incidentes": _calc_total_incidentes_cliente,
    "incidentes_activos": _calc_incidentes_activos_cliente,
    "ultimo_incidente": _calc_ultimo_incidente,
    "total_gastado": _calc_total_gastado,
    "vehiculo": _calc_vehiculo,
}


def reporte_voz_cliente(db: Session, usuario_id: int, url_audio: str) -> dict:
    cliente = db.query(Cliente).filter(Cliente.usuario_id == usuario_id, Cliente.deleted == False).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="No tienes un perfil de cliente registrado.")

    analisis = analizar_consulta_voz(url_audio, METRICAS_CLIENTE)
    datos = {m: _DISPATCH_CLIENTE[m](db, usuario_id) for m in analisis["metricas_solicitadas"]}

    return {"transcripcion": analisis["transcripcion"], "datos": datos}