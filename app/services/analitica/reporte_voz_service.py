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
from app.models.pagos.detalle_orden import DetalleOrden
from app.models.perfiles.cliente import Cliente
from app.models.perfiles.taller import Taller
from app.models.perfiles.tecnico import Tecnico
from app.models.perfiles.servicio_taller import ServicioTaller
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
    "ingresos_periodo",
    "ingresos_totales",
    "tecnicos",
    "servicio_mas_solicitado",
    "servicio_menos_solicitado",
    "asignaciones_periodo",
    "incidentes_atendidos",
    "incidentes_por_categoria",
]

METRICAS_TENANT = [
    "total_talleres",
    "total_incidentes",
    "incidentes_periodo",
    "incidentes_activos",
    "incidentes_pendientes",
    "incidentes_cancelados",
    "tasa_cancelacion",
    "incidentes_por_estado",
    "incidentes_por_prioridad",
    "incidentes_por_categoria",
    "ingresos_periodo",
    "ingresos_totales",
    "ingresos_por_taller",
    "ticket_promedio",
    "total_transacciones",
    "taller_top",
    "taller_mas_ingresos",
    "taller_menos_ingresos",
    "taller_mas_incidentes",
    "taller_mejor_calificado",
    "taller_peor_calificado",
    "taller_sin_actividad",
    "total_ordenes_completadas",
    "ordenes_en_curso",
    "promedio_estrellas_tenant",
    "tecnicos_totales",
    "tecnicos_por_taller",
]

METRICAS_CLIENTE = [
    "total_incidentes",
    "incidentes_activos",
    "ultimo_incidente",
    "total_gastado",
    "gasto_periodo",
    "taller_mas_usado",
    "vehiculo",
    "incidentes_por_categoria",
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
    """Transcribe el audio, identifica métricas y extrae rango de fechas si se menciona."""
    if not _API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY_VOZ no configurada.")

    lista = "\n".join(f"- {m}" for m in metricas_disponibles)
    ahora = datetime.now()
    hoy = ahora.strftime("%Y-%m-%d")
    anio = ahora.year
    mes = ahora.month
    dia_semana = ahora.weekday()
    lunes = (ahora.replace(day=ahora.day - dia_semana)).strftime("%Y-%m-%d")
    domingo = (ahora.replace(day=ahora.day - dia_semana + 6)).strftime("%Y-%m-%d")
    mes_actual_inicio = ahora.replace(day=1).strftime("%Y-%m-%d")
    mes_pasado = mes - 1 if mes > 1 else 12
    anio_mes_pasado = anio if mes > 1 else anio - 1
    import calendar
    ultimo_dia_mes_pasado = calendar.monthrange(anio_mes_pasado, mes_pasado)[1]
    mes_pasado_inicio = f"{anio_mes_pasado}-{mes_pasado:02d}-01"
    mes_pasado_fin = f"{anio_mes_pasado}-{mes_pasado:02d}-{ultimo_dia_mes_pasado:02d}"

    prompt = f"""Eres un asistente de reportes para un sistema de emergencias vehiculares.
Hoy es {hoy}. Usa esta fecha como referencia para calcular fechas relativas.

Métricas disponibles:
{lista}

Devuelve estrictamente un JSON con esta estructura:
{{
  "transcripcion": "texto exacto del audio",
  "metricas_solicitadas": ["lista", "de", "metricas"],
  "solicita_todo": true o false,
  "fecha_inicio": "YYYY-MM-DD o null",
  "fecha_fin": "YYYY-MM-DD o null",
  "categorias_filtro": ["Motor", "Llanta"] o null
}}

Categorias disponibles para incidentes_por_categoria: Motor, Choque, Llanta, Bateria, Otros
Reglas para categorias_filtro:
- Si pide una o varias categorias especificas -> lista con esas categorias (ej. ["Llanta", "Motor"])
- Si pide todas las categorias o no especifica -> null

Reglas para fechas (calcula las fechas exactas, no devuelvas texto relativo):
- "hoy"                    -> fecha_inicio: {hoy}, fecha_fin: {hoy}
- "esta semana"            -> fecha_inicio: {lunes}, fecha_fin: {domingo}
- "la semana pasada"       -> fecha_inicio: lunes de la semana anterior, fecha_fin: domingo de la semana anterior
- "este mes"               -> fecha_inicio: {mes_actual_inicio}, fecha_fin: {hoy}
- "el mes pasado"          -> fecha_inicio: {mes_pasado_inicio}, fecha_fin: {mes_pasado_fin}
- "este año"               -> fecha_inicio: {anio}-01-01, fecha_fin: {hoy}
- "el año pasado"          -> fecha_inicio: {anio - 1}-01-01, fecha_fin: {anio - 1}-12-31
- "hace N dias"            -> fecha_inicio: {hoy} menos N dias, fecha_fin: {hoy}
- "hace N semanas"         -> fecha_inicio: {hoy} menos N*7 dias, fecha_fin: {hoy}
- "hace N meses"           -> fecha_inicio: mismo dia N meses atras, fecha_fin: {hoy}
- "desde el DD de MES"     -> fecha_inicio: ese dia, fecha_fin: {hoy}
- "del DD de MES al DD de MES" -> extrae ambas fechas exactas
- "en MES" o "de MES"      -> primer y ultimo dia de ese mes en el año {anio}
- Sin fechas               -> fecha_inicio: null, fecha_fin: null

Reglas para metricas:
- Si pide resumen general o todas las metricas -> solicita_todo: true
- Solo incluye metricas de la lista proporcionada."""

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
        resultado.setdefault("fecha_inicio", None)
        resultado.setdefault("fecha_fin", None)
        if not isinstance(resultado.get("categorias_filtro"), list):
            resultado["categorias_filtro"] = None
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error en IA al procesar el audio: {e}")


# ---------------------------------------------------------------------------
# Helper compartido — incidentes por categoría
# ---------------------------------------------------------------------------

from app.models.ia.analisis import Analisis as _Analisis


def _query_incidentes_por_categoria(db, query_base, fi, ff, categorias):
    """
    query_base: query de Incidente ya filtrado por rol (tenant_id, usuario_id, taller)
    Devuelve dict { categoria: cantidad }
    """
    q = (
        query_base
        .join(_Analisis, _Analisis.incidente_id == Incidente.id, isouter=True)
        .filter(
            Incidente.fecha_hora >= fi,
            Incidente.fecha_hora <= ff,
        )
        .with_entities(
            func.coalesce(_Analisis.categoria_problema, "Sin clasificar").label("cat"),
            func.count(Incidente.id).label("c"),
        )
        .group_by(func.coalesce(_Analisis.categoria_problema, "Sin clasificar"))
    )
    rows = q.all()
    resultado = {r.cat: r.c for r in rows}
    if categorias:
        resultado = {k: v for k, v in resultado.items() if k in categorias}
    return resultado if resultado else {}


# ---------------------------------------------------------------------------
# Helpers de fechas
# ---------------------------------------------------------------------------

def _rango_mes_actual():
    now = datetime.now(timezone.utc)
    inicio = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    fin = now
    return inicio, fin


def _parsear_fechas(fecha_inicio_str, fecha_fin_str):
    """Convierte strings ISO a datetime. Si solo viene inicio, fin = hoy. Si ninguno, mes actual."""
    hoy = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59, microsecond=0)
    if fecha_inicio_str:
        try:
            fi = datetime.fromisoformat(fecha_inicio_str).replace(tzinfo=timezone.utc)
            if fecha_fin_str:
                ff = datetime.fromisoformat(fecha_fin_str).replace(
                    hour=23, minute=59, second=59, tzinfo=timezone.utc
                )
            else:
                ff = hoy
            return fi, ff
        except (ValueError, TypeError):
            pass
    return _rango_mes_actual()


# ---------------------------------------------------------------------------
# Taller — métricas
# ---------------------------------------------------------------------------

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


def _calc_ordenes_activas(db, taller_id, fi, ff):
    return _base_ordenes_taller(db, taller_id).filter(
        OrdenServicio.estado.in_([
            EstadoOperacion.EN_CAMINO,
            EstadoOperacion.DIAGNOSTICANDO,
            EstadoOperacion.REPARANDO,
        ])
    ).count()


def _calc_ordenes_completadas(db, taller_id, fi, ff):
    return _base_ordenes_taller(db, taller_id).filter(
        OrdenServicio.estado == EstadoOperacion.FINALIZADO,
        OrdenServicio.fecha_hora_fin >= fi,
        OrdenServicio.fecha_hora_fin <= ff,
    ).count()


def _calc_promedio_estrellas(db, taller_id, fi, ff):
    val = (
        db.query(func.avg(OrdenServicio.estrellas))
        .join(Cotizacion, Cotizacion.id == OrdenServicio.cotizacion_id)
        .join(AsignacionCandidato, AsignacionCandidato.id == Cotizacion.asignacion_candidato_id)
        .filter(
            AsignacionCandidato.taller_id == taller_id,
            OrdenServicio.estrellas.isnot(None),
            OrdenServicio.fecha_hora >= fi,
            OrdenServicio.fecha_hora <= ff,
            OrdenServicio.deleted == False,
        )
        .scalar()
    )
    return round(float(val), 2) if val else None


def _base_transacciones_taller(db, taller_id):
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


def _calc_ingresos_periodo(db, taller_id, fi, ff):
    val = _base_transacciones_taller(db, taller_id).filter(
        Transaccion.fecha_hora >= fi,
        Transaccion.fecha_hora <= ff,
    ).with_entities(func.sum(Transaccion.monto_cobrado)).scalar()
    return round(float(val), 2) if val else 0.0


def _calc_ingresos_totales(db, taller_id, fi, ff):
    val = _base_transacciones_taller(db, taller_id).with_entities(
        func.sum(Transaccion.monto_cobrado)
    ).scalar()
    return round(float(val), 2) if val else 0.0


def _calc_tecnicos(db, taller_id, fi, ff):
    tecnicos = db.query(Tecnico).filter(
        Tecnico.taller_id == taller_id,
        Tecnico.deleted == False,
    ).all()
    return [{"nombre": f"{t.nombre} {t.apellido}", "telefono": t.telefono} for t in tecnicos]


def _calc_servicio_mas_solicitado(db, taller_id, fi, ff):
    row = (
        db.query(ServicioTaller.nombre, func.count(DetalleOrden.id).label("c"))
        .join(DetalleOrden, DetalleOrden.servicio_taller_id == ServicioTaller.id)
        .join(OrdenServicio, OrdenServicio.id == DetalleOrden.orden_servicio_id)
        .join(Cotizacion, Cotizacion.id == OrdenServicio.cotizacion_id)
        .join(AsignacionCandidato, AsignacionCandidato.id == Cotizacion.asignacion_candidato_id)
        .filter(
            AsignacionCandidato.taller_id == taller_id,
            OrdenServicio.fecha_hora >= fi,
            OrdenServicio.fecha_hora <= ff,
            DetalleOrden.deleted == False,
            OrdenServicio.deleted == False,
        )
        .group_by(ServicioTaller.nombre)
        .order_by(func.count(DetalleOrden.id).desc())
        .first()
    )
    return {"nombre": row.nombre, "cantidad": row.c} if row else None


def _calc_servicio_menos_solicitado(db, taller_id, fi, ff):
    row = (
        db.query(ServicioTaller.nombre, func.count(DetalleOrden.id).label("c"))
        .join(DetalleOrden, DetalleOrden.servicio_taller_id == ServicioTaller.id)
        .join(OrdenServicio, OrdenServicio.id == DetalleOrden.orden_servicio_id)
        .join(Cotizacion, Cotizacion.id == OrdenServicio.cotizacion_id)
        .join(AsignacionCandidato, AsignacionCandidato.id == Cotizacion.asignacion_candidato_id)
        .filter(
            AsignacionCandidato.taller_id == taller_id,
            OrdenServicio.fecha_hora >= fi,
            OrdenServicio.fecha_hora <= ff,
            DetalleOrden.deleted == False,
            OrdenServicio.deleted == False,
        )
        .group_by(ServicioTaller.nombre)
        .order_by(func.count(DetalleOrden.id).asc())
        .first()
    )
    return {"nombre": row.nombre, "cantidad": row.c} if row else None


def _calc_asignaciones_periodo(db, taller_id, fi, ff):
    return (
        db.query(func.count(AsignacionCandidato.id))
        .filter(
            AsignacionCandidato.taller_id == taller_id,
            AsignacionCandidato.created_at >= fi,
            AsignacionCandidato.created_at <= ff,
            AsignacionCandidato.deleted == False,
        )
        .scalar() or 0
    )


def _calc_incidentes_atendidos(db, taller_id, fi, ff):
    return (
        db.query(func.count(AsignacionCandidato.id))
        .join(Incidente, Incidente.id == AsignacionCandidato.incidente_id)
        .filter(
            AsignacionCandidato.taller_id == taller_id,
            AsignacionCandidato.estado == "Aceptado",
            Incidente.fecha_hora >= fi,
            Incidente.fecha_hora <= ff,
            AsignacionCandidato.deleted == False,
            Incidente.deleted == False,
        )
        .scalar() or 0
    )


def _calc_incidentes_por_categoria_taller(db, taller_id, fi, ff, categorias=None):
    base = (
        db.query(Incidente)
        .join(AsignacionCandidato, AsignacionCandidato.incidente_id == Incidente.id)
        .filter(
            AsignacionCandidato.taller_id == taller_id,
            AsignacionCandidato.estado == "Aceptado",
            AsignacionCandidato.deleted == False,
            Incidente.deleted == False,
        )
    )
    return _query_incidentes_por_categoria(db, base, fi, ff, categorias)


_DISPATCH_TALLER = {
    "ordenes_activas": _calc_ordenes_activas,
    "ordenes_completadas": _calc_ordenes_completadas,
    "promedio_estrellas": _calc_promedio_estrellas,
    "ingresos_periodo": _calc_ingresos_periodo,
    "ingresos_totales": _calc_ingresos_totales,
    "tecnicos": _calc_tecnicos,
    "servicio_mas_solicitado": _calc_servicio_mas_solicitado,
    "servicio_menos_solicitado": _calc_servicio_menos_solicitado,
    "asignaciones_periodo": _calc_asignaciones_periodo,
    "incidentes_atendidos": _calc_incidentes_atendidos,
    "incidentes_por_categoria": _calc_incidentes_por_categoria_taller,
}


def reporte_voz_taller(db: Session, usuario_id: int, url_audio: str) -> dict:
    taller = db.query(Taller).filter(Taller.usuario_id == usuario_id, Taller.deleted == False).first()
    if not taller:
        raise HTTPException(status_code=404, detail="No tienes un taller registrado.")

    analisis = analizar_consulta_voz(url_audio, METRICAS_TALLER)
    fi, ff = _parsear_fechas(analisis["fecha_inicio"], analisis["fecha_fin"])
    cats = analisis.get("categorias_filtro")
    datos = {
        m: (_DISPATCH_TALLER[m](db, taller.id, fi, ff, cats)
            if m == "incidentes_por_categoria"
            else _DISPATCH_TALLER[m](db, taller.id, fi, ff))
        for m in analisis["metricas_solicitadas"]
    }

    return {
        "transcripcion": analisis["transcripcion"],
        "fecha_inicio": fi.date().isoformat(),
        "fecha_fin": ff.date().isoformat(),
        "datos": datos,
    }


# ---------------------------------------------------------------------------
# Tenant — métricas
# ---------------------------------------------------------------------------

def _calc_total_talleres(db, tenant_id, fi, ff):  # noqa: ARG001
    return db.query(func.count(Taller.id)).filter(Taller.tenant_id == tenant_id, Taller.deleted == False).scalar() or 0


def _calc_total_incidentes_tenant(db, tenant_id, fi, ff):  # noqa: ARG001
    return db.query(func.count(Incidente.id)).filter(Incidente.tenant_id == tenant_id, Incidente.deleted == False).scalar() or 0


def _calc_incidentes_periodo_tenant(db, tenant_id, fi, ff):
    return (
        db.query(func.count(Incidente.id))
        .filter(
            Incidente.tenant_id == tenant_id,
            Incidente.fecha_hora >= fi,
            Incidente.fecha_hora <= ff,
            Incidente.deleted == False,
        )
        .scalar() or 0
    )


def _calc_incidentes_activos_tenant(db, tenant_id, fi, ff):  # noqa: ARG001
    return (
        db.query(func.count(Incidente.id))
        .filter(
            Incidente.tenant_id == tenant_id,
            Incidente.estado == EstadoIncidente.EN_PROCESO,
            Incidente.deleted == False,
        )
        .scalar() or 0
    )


def _calc_incidentes_por_estado(db, tenant_id, fi, ff):
    rows = (
        db.query(Incidente.estado, func.count(Incidente.id).label("c"))
        .filter(
            Incidente.tenant_id == tenant_id,
            Incidente.fecha_hora >= fi,
            Incidente.fecha_hora <= ff,
            Incidente.deleted == False,
        )
        .group_by(Incidente.estado)
        .all()
    )
    return {r.estado: r.c for r in rows} if rows else {}


def _calc_incidentes_por_prioridad(db, tenant_id, fi, ff):
    rows = (
        db.query(Incidente.prioridad, func.count(Incidente.id).label("c"))
        .filter(
            Incidente.tenant_id == tenant_id,
            Incidente.fecha_hora >= fi,
            Incidente.fecha_hora <= ff,
            Incidente.deleted == False,
        )
        .group_by(Incidente.prioridad)
        .all()
    )
    return {r.prioridad: r.c for r in rows} if rows else {}


def _calc_ingresos_periodo_tenant(db, tenant_id, fi, ff):
    val = (
        db.query(func.sum(Transaccion.monto_cobrado))
        .filter(
            Transaccion.tenant_id == tenant_id,
            Transaccion.estado == EstadoTransaccion.PAGADO,
            Transaccion.fecha_hora >= fi,
            Transaccion.fecha_hora <= ff,
            Transaccion.deleted == False,
        )
        .scalar()
    )
    return round(float(val), 2) if val else 0.0


def _calc_ingresos_totales_tenant(db, tenant_id, fi, ff):  # noqa: ARG001
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


def _base_ordenes_tenant(db, tenant_id, fi, ff):
    return (
        db.query(OrdenServicio)
        .join(Cotizacion, Cotizacion.id == OrdenServicio.cotizacion_id)
        .join(AsignacionCandidato, AsignacionCandidato.id == Cotizacion.asignacion_candidato_id)
        .join(Taller, Taller.id == AsignacionCandidato.taller_id)
        .filter(
            Taller.tenant_id == tenant_id,
            OrdenServicio.fecha_hora >= fi,
            OrdenServicio.fecha_hora <= ff,
            OrdenServicio.deleted == False,
            Taller.deleted == False,
        )
    )


def _calc_taller_top(db, tenant_id, fi, ff):
    row = (
        db.query(Taller.nombre, func.count(OrdenServicio.id).label("c"))
        .join(AsignacionCandidato, AsignacionCandidato.taller_id == Taller.id)
        .join(Cotizacion, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .join(OrdenServicio, OrdenServicio.cotizacion_id == Cotizacion.id)
        .filter(
            Taller.tenant_id == tenant_id,
            OrdenServicio.estado == EstadoOperacion.FINALIZADO,
            OrdenServicio.fecha_hora >= fi,
            OrdenServicio.fecha_hora <= ff,
            Taller.deleted == False,
            OrdenServicio.deleted == False,
        )
        .group_by(Taller.nombre)
        .order_by(func.count(OrdenServicio.id).desc())
        .first()
    )
    return {"nombre": row.nombre, "ordenes": row.c} if row else None


def _calc_taller_mas_ingresos(db, tenant_id, fi, ff):
    row = (
        db.query(Taller.nombre, func.sum(Transaccion.monto_cobrado).label("total"))
        .join(AsignacionCandidato, AsignacionCandidato.taller_id == Taller.id)
        .join(Cotizacion, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .join(OrdenServicio, OrdenServicio.cotizacion_id == Cotizacion.id)
        .join(Transaccion, Transaccion.orden_servicio_id == OrdenServicio.id)
        .filter(
            Taller.tenant_id == tenant_id,
            Transaccion.estado == EstadoTransaccion.PAGADO,
            Transaccion.fecha_hora >= fi,
            Transaccion.fecha_hora <= ff,
            Taller.deleted == False,
            Transaccion.deleted == False,
        )
        .group_by(Taller.nombre)
        .order_by(func.sum(Transaccion.monto_cobrado).desc())
        .first()
    )
    return {"nombre": row.nombre, "ingresos": round(float(row.total), 2)} if row else None


def _calc_taller_mas_incidentes(db, tenant_id, fi, ff):
    row = (
        db.query(Taller.nombre, func.count(AsignacionCandidato.id).label("c"))
        .join(AsignacionCandidato, AsignacionCandidato.taller_id == Taller.id)
        .join(Incidente, Incidente.id == AsignacionCandidato.incidente_id)
        .filter(
            Taller.tenant_id == tenant_id,
            AsignacionCandidato.estado == "Aceptado",
            Incidente.fecha_hora >= fi,
            Incidente.fecha_hora <= ff,
            Taller.deleted == False,
            AsignacionCandidato.deleted == False,
        )
        .group_by(Taller.nombre)
        .order_by(func.count(AsignacionCandidato.id).desc())
        .first()
    )
    return {"nombre": row.nombre, "incidentes": row.c} if row else None


def _calc_total_ordenes_completadas(db, tenant_id, fi, ff):
    return _base_ordenes_tenant(db, tenant_id, fi, ff).filter(
        OrdenServicio.estado == EstadoOperacion.FINALIZADO
    ).count()


def _calc_promedio_estrellas_tenant(db, tenant_id, fi, ff):
    val = (
        _base_ordenes_tenant(db, tenant_id, fi, ff)
        .filter(OrdenServicio.estrellas.isnot(None))
        .with_entities(func.avg(OrdenServicio.estrellas))
        .scalar()
    )
    return round(float(val), 2) if val else None


def _calc_tecnicos_totales(db, tenant_id, fi, ff):  # noqa: ARG001
    return (
        db.query(func.count(Tecnico.id))
        .join(Taller, Taller.id == Tecnico.taller_id)
        .filter(
            Taller.tenant_id == tenant_id,
            Tecnico.deleted == False,
            Taller.deleted == False,
        )
        .scalar() or 0
    )


def _calc_incidentes_por_categoria_tenant(db, tenant_id, fi, ff, categorias=None):
    base = (
        db.query(Incidente)
        .filter(Incidente.tenant_id == tenant_id, Incidente.deleted == False)
    )
    return _query_incidentes_por_categoria(db, base, fi, ff, categorias)


def _calc_taller_menos_ingresos(db, tenant_id, fi, ff):
    row = (
        db.query(Taller.nombre, func.sum(Transaccion.monto_cobrado).label("total"))
        .join(AsignacionCandidato, AsignacionCandidato.taller_id == Taller.id)
        .join(Cotizacion, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .join(OrdenServicio, OrdenServicio.cotizacion_id == Cotizacion.id)
        .join(Transaccion, Transaccion.orden_servicio_id == OrdenServicio.id)
        .filter(
            Taller.tenant_id == tenant_id,
            Transaccion.estado == EstadoTransaccion.PAGADO,
            Transaccion.fecha_hora >= fi,
            Transaccion.fecha_hora <= ff,
            Taller.deleted == False,
            Transaccion.deleted == False,
        )
        .group_by(Taller.nombre)
        .order_by(func.sum(Transaccion.monto_cobrado).asc())
        .first()
    )
    return {"nombre": row.nombre, "ingresos": round(float(row.total), 2)} if row else None


def _calc_taller_sin_actividad(db, tenant_id, fi, ff):
    talleres_con_orden = (
        db.query(Taller.id)
        .join(AsignacionCandidato, AsignacionCandidato.taller_id == Taller.id)
        .join(Cotizacion, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .join(OrdenServicio, OrdenServicio.cotizacion_id == Cotizacion.id)
        .filter(
            Taller.tenant_id == tenant_id,
            OrdenServicio.fecha_hora >= fi,
            OrdenServicio.fecha_hora <= ff,
            OrdenServicio.deleted == False,
        )
        .subquery()
    )
    rows = (
        db.query(Taller.nombre)
        .filter(
            Taller.tenant_id == tenant_id,
            Taller.deleted == False,
            ~Taller.id.in_(talleres_con_orden),
        )
        .all()
    )
    return [r.nombre for r in rows] if rows else []


def _calc_taller_mejor_calificado(db, tenant_id, fi, ff):
    row = (
        db.query(Taller.nombre, func.avg(OrdenServicio.estrellas).label("avg"))
        .join(AsignacionCandidato, AsignacionCandidato.taller_id == Taller.id)
        .join(Cotizacion, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .join(OrdenServicio, OrdenServicio.cotizacion_id == Cotizacion.id)
        .filter(
            Taller.tenant_id == tenant_id,
            OrdenServicio.estrellas.isnot(None),
            OrdenServicio.fecha_hora >= fi,
            OrdenServicio.fecha_hora <= ff,
            Taller.deleted == False,
            OrdenServicio.deleted == False,
        )
        .group_by(Taller.nombre)
        .order_by(func.avg(OrdenServicio.estrellas).desc())
        .first()
    )
    return {"nombre": row.nombre, "promedio_estrellas": round(float(row.avg), 2)} if row else None


def _calc_taller_peor_calificado(db, tenant_id, fi, ff):
    row = (
        db.query(Taller.nombre, func.avg(OrdenServicio.estrellas).label("avg"))
        .join(AsignacionCandidato, AsignacionCandidato.taller_id == Taller.id)
        .join(Cotizacion, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .join(OrdenServicio, OrdenServicio.cotizacion_id == Cotizacion.id)
        .filter(
            Taller.tenant_id == tenant_id,
            OrdenServicio.estrellas.isnot(None),
            OrdenServicio.fecha_hora >= fi,
            OrdenServicio.fecha_hora <= ff,
            Taller.deleted == False,
            OrdenServicio.deleted == False,
        )
        .group_by(Taller.nombre)
        .order_by(func.avg(OrdenServicio.estrellas).asc())
        .first()
    )
    return {"nombre": row.nombre, "promedio_estrellas": round(float(row.avg), 2)} if row else None


def _calc_incidentes_cancelados(db, tenant_id, fi, ff):
    return (
        db.query(func.count(Incidente.id))
        .filter(
            Incidente.tenant_id == tenant_id,
            Incidente.estado == EstadoIncidente.CANCELADO,
            Incidente.fecha_hora >= fi,
            Incidente.fecha_hora <= ff,
            Incidente.deleted == False,
        )
        .scalar() or 0
    )


def _calc_tasa_cancelacion(db, tenant_id, fi, ff):
    total = (
        db.query(func.count(Incidente.id))
        .filter(
            Incidente.tenant_id == tenant_id,
            Incidente.fecha_hora >= fi,
            Incidente.fecha_hora <= ff,
            Incidente.deleted == False,
        )
        .scalar() or 0
    )
    cancelados = _calc_incidentes_cancelados(db, tenant_id, fi, ff)
    porcentaje = round(cancelados / total * 100, 2) if total > 0 else 0.0
    return {"cancelados": cancelados, "total": total, "porcentaje": porcentaje}


def _calc_incidentes_pendientes(db, tenant_id, fi, ff):  # noqa: ARG001
    return (
        db.query(func.count(Incidente.id))
        .filter(
            Incidente.tenant_id == tenant_id,
            Incidente.estado == EstadoIncidente.PENDIENTE,
            Incidente.deleted == False,
        )
        .scalar() or 0
    )


def _calc_ordenes_en_curso(db, tenant_id, fi, ff):  # noqa: ARG001
    return (
        db.query(func.count(OrdenServicio.id))
        .join(Cotizacion, Cotizacion.id == OrdenServicio.cotizacion_id)
        .join(AsignacionCandidato, AsignacionCandidato.id == Cotizacion.asignacion_candidato_id)
        .join(Taller, Taller.id == AsignacionCandidato.taller_id)
        .filter(
            Taller.tenant_id == tenant_id,
            OrdenServicio.estado.in_([
                EstadoOperacion.EN_CAMINO,
                EstadoOperacion.DIAGNOSTICANDO,
                EstadoOperacion.REPARANDO,
            ]),
            OrdenServicio.deleted == False,
            Taller.deleted == False,
        )
        .scalar() or 0
    )


def _calc_total_transacciones(db, tenant_id, fi, ff):
    return (
        db.query(func.count(Transaccion.id))
        .filter(
            Transaccion.tenant_id == tenant_id,
            Transaccion.estado == EstadoTransaccion.PAGADO,
            Transaccion.fecha_hora >= fi,
            Transaccion.fecha_hora <= ff,
            Transaccion.deleted == False,
        )
        .scalar() or 0
    )


def _calc_ticket_promedio(db, tenant_id, fi, ff):
    val = (
        db.query(func.avg(Transaccion.monto_cobrado))
        .filter(
            Transaccion.tenant_id == tenant_id,
            Transaccion.estado == EstadoTransaccion.PAGADO,
            Transaccion.fecha_hora >= fi,
            Transaccion.fecha_hora <= ff,
            Transaccion.deleted == False,
        )
        .scalar()
    )
    return round(float(val), 2) if val else 0.0


def _calc_ingresos_por_taller(db, tenant_id, fi, ff):
    rows = (
        db.query(Taller.nombre, func.sum(Transaccion.monto_cobrado).label("total"))
        .join(AsignacionCandidato, AsignacionCandidato.taller_id == Taller.id)
        .join(Cotizacion, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .join(OrdenServicio, OrdenServicio.cotizacion_id == Cotizacion.id)
        .join(Transaccion, Transaccion.orden_servicio_id == OrdenServicio.id)
        .filter(
            Taller.tenant_id == tenant_id,
            Transaccion.estado == EstadoTransaccion.PAGADO,
            Transaccion.fecha_hora >= fi,
            Transaccion.fecha_hora <= ff,
            Taller.deleted == False,
            Transaccion.deleted == False,
        )
        .group_by(Taller.nombre)
        .order_by(func.sum(Transaccion.monto_cobrado).desc())
        .all()
    )
    return {r.nombre: round(float(r.total), 2) for r in rows} if rows else {}


def _calc_tecnicos_por_taller(db, tenant_id, fi, ff):  # noqa: ARG001
    rows = (
        db.query(Taller.nombre, func.count(Tecnico.id).label("c"))
        .join(Tecnico, Tecnico.taller_id == Taller.id)
        .filter(
            Taller.tenant_id == tenant_id,
            Taller.deleted == False,
            Tecnico.deleted == False,
        )
        .group_by(Taller.nombre)
        .all()
    )
    return {r.nombre: r.c for r in rows} if rows else {}


_DISPATCH_TENANT = {
    "total_talleres": _calc_total_talleres,
    "total_incidentes": _calc_total_incidentes_tenant,
    "incidentes_periodo": _calc_incidentes_periodo_tenant,
    "incidentes_activos": _calc_incidentes_activos_tenant,
    "incidentes_pendientes": _calc_incidentes_pendientes,
    "incidentes_cancelados": _calc_incidentes_cancelados,
    "tasa_cancelacion": _calc_tasa_cancelacion,
    "incidentes_por_estado": _calc_incidentes_por_estado,
    "incidentes_por_prioridad": _calc_incidentes_por_prioridad,
    "incidentes_por_categoria": _calc_incidentes_por_categoria_tenant,
    "ingresos_periodo": _calc_ingresos_periodo_tenant,
    "ingresos_totales": _calc_ingresos_totales_tenant,
    "ingresos_por_taller": _calc_ingresos_por_taller,
    "ticket_promedio": _calc_ticket_promedio,
    "total_transacciones": _calc_total_transacciones,
    "taller_top": _calc_taller_top,
    "taller_mas_ingresos": _calc_taller_mas_ingresos,
    "taller_menos_ingresos": _calc_taller_menos_ingresos,
    "taller_mas_incidentes": _calc_taller_mas_incidentes,
    "taller_mejor_calificado": _calc_taller_mejor_calificado,
    "taller_peor_calificado": _calc_taller_peor_calificado,
    "taller_sin_actividad": _calc_taller_sin_actividad,
    "total_ordenes_completadas": _calc_total_ordenes_completadas,
    "ordenes_en_curso": _calc_ordenes_en_curso,
    "promedio_estrellas_tenant": _calc_promedio_estrellas_tenant,
    "tecnicos_totales": _calc_tecnicos_totales,
    "tecnicos_por_taller": _calc_tecnicos_por_taller,
}


def reporte_voz_tenant(db: Session, tenant_id: int, url_audio: str) -> dict:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.deleted == False).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado.")

    analisis = analizar_consulta_voz(url_audio, METRICAS_TENANT)
    fi, ff = _parsear_fechas(analisis["fecha_inicio"], analisis["fecha_fin"])
    cats = analisis.get("categorias_filtro")
    datos = {
        m: (_DISPATCH_TENANT[m](db, tenant_id, fi, ff, cats)
            if m == "incidentes_por_categoria"
            else _DISPATCH_TENANT[m](db, tenant_id, fi, ff))
        for m in analisis["metricas_solicitadas"]
    }

    return {
        "transcripcion": analisis["transcripcion"],
        "fecha_inicio": fi.date().isoformat(),
        "fecha_fin": ff.date().isoformat(),
        "datos": datos,
    }


# ---------------------------------------------------------------------------
# Cliente — métricas
# ---------------------------------------------------------------------------

def _calc_total_incidentes_cliente(db, usuario_id):
    return (
        db.query(func.count(Incidente.id))
        .filter(Incidente.usuario_id == usuario_id, Incidente.deleted == False)
        .scalar() or 0
    )


def _calc_incidentes_activos_cliente(db, usuario_id):
    return (
        db.query(func.count(Incidente.id))
        .filter(
            Incidente.usuario_id == usuario_id,
            Incidente.estado == EstadoIncidente.EN_PROCESO,
            Incidente.deleted == False,
        )
        .scalar() or 0
    )


def _calc_ultimo_incidente(db, usuario_id):
    inc = (
        db.query(Incidente)
        .filter(Incidente.usuario_id == usuario_id, Incidente.deleted == False)
        .order_by(Incidente.fecha_hora.desc())
        .first()
    )
    if not inc:
        return None
    return {"fecha": inc.fecha_hora.isoformat(), "estado": inc.estado.value}


def _calc_total_gastado(db, usuario_id):
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


def _calc_vehiculo(db, usuario_id):
    cliente = db.query(Cliente).filter(Cliente.usuario_id == usuario_id, Cliente.deleted == False).first()
    if not cliente or not cliente.vehiculo:
        return None
    return {"placa": cliente.vehiculo.placa, "modelo": cliente.vehiculo.modelo}


def _calc_gasto_periodo(db, usuario_id, fi, ff):
    val = (
        db.query(func.sum(Transaccion.monto_cobrado))
        .join(OrdenServicio, OrdenServicio.id == Transaccion.orden_servicio_id)
        .join(Cotizacion, Cotizacion.id == OrdenServicio.cotizacion_id)
        .join(AsignacionCandidato, AsignacionCandidato.id == Cotizacion.asignacion_candidato_id)
        .join(Incidente, Incidente.id == AsignacionCandidato.incidente_id)
        .filter(
            Incidente.usuario_id == usuario_id,
            Transaccion.estado == EstadoTransaccion.PAGADO,
            Transaccion.fecha_hora >= fi,
            Transaccion.fecha_hora <= ff,
            Transaccion.deleted == False,
        )
        .scalar()
    )
    return round(float(val), 2) if val else 0.0


def _calc_taller_mas_usado(db, usuario_id, fi, ff):
    row = (
        db.query(Taller.nombre, func.count(AsignacionCandidato.id).label("c"))
        .join(AsignacionCandidato, AsignacionCandidato.taller_id == Taller.id)
        .join(Incidente, Incidente.id == AsignacionCandidato.incidente_id)
        .filter(
            Incidente.usuario_id == usuario_id,
            AsignacionCandidato.estado == "Aceptado",
            Incidente.fecha_hora >= fi,
            Incidente.fecha_hora <= ff,
            AsignacionCandidato.deleted == False,
            Incidente.deleted == False,
        )
        .group_by(Taller.nombre)
        .order_by(func.count(AsignacionCandidato.id).desc())
        .first()
    )
    return {"nombre": row.nombre, "veces": row.c} if row else None


def _calc_incidentes_por_categoria_cliente(db, usuario_id, fi, ff, categorias=None):
    base = (
        db.query(Incidente)
        .filter(Incidente.usuario_id == usuario_id, Incidente.deleted == False)
    )
    return _query_incidentes_por_categoria(db, base, fi, ff, categorias)


_DISPATCH_CLIENTE = {
    "total_incidentes": _calc_total_incidentes_cliente,
    "incidentes_activos": _calc_incidentes_activos_cliente,
    "ultimo_incidente": _calc_ultimo_incidente,
    "total_gastado": _calc_total_gastado,
    "vehiculo": _calc_vehiculo,
    "gasto_periodo": _calc_gasto_periodo,
    "taller_mas_usado": _calc_taller_mas_usado,
    "incidentes_por_categoria": _calc_incidentes_por_categoria_cliente,
}


def reporte_voz_cliente(db: Session, usuario_id: int, url_audio: str) -> dict:
    cliente = db.query(Cliente).filter(Cliente.usuario_id == usuario_id, Cliente.deleted == False).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="No tienes un perfil de cliente registrado.")

    analisis = analizar_consulta_voz(url_audio, METRICAS_CLIENTE)
    fi, ff = _parsear_fechas(analisis["fecha_inicio"], analisis["fecha_fin"])
    cats = analisis.get("categorias_filtro")
    metricas_con_fechas = {"gasto_periodo", "taller_mas_usado", "incidentes_por_categoria"}
    datos = {}
    for m in analisis["metricas_solicitadas"]:
        if m == "incidentes_por_categoria":
            datos[m] = _DISPATCH_CLIENTE[m](db, usuario_id, fi, ff, cats)
        elif m in metricas_con_fechas:
            datos[m] = _DISPATCH_CLIENTE[m](db, usuario_id, fi, ff)
        else:
            datos[m] = _DISPATCH_CLIENTE[m](db, usuario_id)

    return {
        "transcripcion": analisis["transcripcion"],
        "fecha_inicio": fi.date().isoformat(),
        "fecha_fin": ff.date().isoformat(),
        "datos": datos,
    }