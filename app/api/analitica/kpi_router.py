from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.services.analitica import kpi_service
from app.schemas.analitica.kpi_schema import (
    TiempoPromedioAsignacionSalida,
    TiempoPromedioLlegadaSalida,
    IncidentesPorTipoSalida,
    TalleresEficientesSalida,
    ZonasIncidentesSalida,
    CasosCanceladosSalida,
    SlaCumplimientoSalida,
)

router = APIRouter(
    prefix="/analitica/kpi",
    tags=["Analítica KPI"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/tiempo-asignacion/{tenant_id}", response_model=TiempoPromedioAsignacionSalida)
def get_tiempo_asignacion(tenant_id: int, db: Session = Depends(get_db)):
    return kpi_service.tiempo_promedio_asignacion(db, tenant_id)


@router.get("/tiempo-llegada/{tenant_id}", response_model=TiempoPromedioLlegadaSalida)
def get_tiempo_llegada(tenant_id: int, db: Session = Depends(get_db)):
    return kpi_service.obtener_tiempo_promedio_llegada(db, tenant_id)


@router.get("/incidentes-por-tipo/{tenant_id}", response_model=IncidentesPorTipoSalida)
def get_incidentes_por_tipo(tenant_id: int, db: Session = Depends(get_db)):
    return kpi_service.obtener_incidentes_por_tipo(db, tenant_id)


@router.get("/talleres-eficientes/{tenant_id}", response_model=TalleresEficientesSalida)
def get_talleres_eficientes(
    tenant_id: int, limite: int = 10, db: Session = Depends(get_db)
):
    return kpi_service.obtener_talleres_mas_eficientes(db, tenant_id, limite)


@router.get("/zonas-incidentes/{tenant_id}", response_model=ZonasIncidentesSalida)
def get_zonas_incidentes(
    tenant_id: int, limite: int = 10, db: Session = Depends(get_db)
):
    return kpi_service.obtener_zonas_con_mas_incidentes(db, tenant_id, limite)


@router.get("/casos-cancelados/{tenant_id}", response_model=CasosCanceladosSalida)
def get_casos_cancelados(tenant_id: int, db: Session = Depends(get_db)):
    return kpi_service.obtener_casos_cancelados(db, tenant_id)


@router.get("/sla-cumplimiento/{tenant_id}", response_model=SlaCumplimientoSalida)
def get_sla_cumplimiento(tenant_id: int, db: Session = Depends(get_db)):
    return kpi_service.calcular_sla_cumplimiento(db, tenant_id)