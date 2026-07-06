from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import Base, engine, SessionLocal
from app.db import seeder

# Tenant debe importarse primero porque otros modelos lo referencian como FK
from app.models.talleres import tenant  # noqa: F401

# Modelos cuentas
from app.models.cuentas import rol, usuario, privilegio, rol_privilegio  # noqa: F401
# Modelos perfiles
from app.models.perfiles import cliente, vehiculo, taller, servicio_taller, tecnico  # noqa: F401
# Modelos emergencias
from app.models.emergencias import incidente, evidencia  # noqa: F401
# Modelos IA
from app.models.ia import analisis  # noqa: F401
# Modelos talleres
from app.models.talleres import asignacion_candidato, cotizacion, orden_servicio  # noqa: F401
# Modelos pagos
from app.models.pagos import detalle_orden, transaccion  # noqa: F401

# APIs cuentas
from app.api.cuentas import auth, rol as rol_api, usuario as usuario_api, privilegio as privilegio_api
# APIs perfiles
from app.api.perfiles import (
    cliente as cliente_api,
    vehiculo as vehiculo_api,
    taller as taller_api,
    servicio_taller as servicio_taller_api,
    tecnico as tecnico_api,
)
# APIs emergencias
from app.api.emergencias import incidente as incidente_api
from app.api.emergencias import evidencia as evidencia_api
# APIs IA
from app.api.ia import procesamiento as ia_procesamiento_api
from app.api.ia import analisis as ia_analisis_api
# APIs talleres
from app.api.talleres import orden_servicio as orden_servicio_api
from app.api.talleres import asignacion_candidato as asignacion_candidato_api
from app.api.talleres import cotizacion as cotizacion_api
from app.api.talleres import tenant as tenant_api
# APIs pagos
from app.api.pagos import detalle_orden as detalle_orden_api
from app.api.pagos import transaccion as transaccion_api
# APIs analítica
from app.api.analitica import kpi_router as kpi_router_api
from app.api.analitica import reporte_voz_router as reporte_voz_api
# Tracking WebSocket
from app.tracking import router as tracking_router

Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    seeder.ejecutar(db)
finally:
    db.close()

app = FastAPI(
    title="AutoSOS",
    description="Backend para gestión de emergencias vehiculares en tiempo real",
    version="1.0.0"
)

origins = [
    "http://localhost:4200",
    "http://localhost",
    "http://127.0.0.1",
    "https://backend-emergencia-vehiculares.onrender.com",
    "https://frontend-emergencia-vehiculares.vercel.app",
    "https://autosos-api.ddns.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cuentas
app.include_router(auth.router)
app.include_router(rol_api.router)
app.include_router(usuario_api.router)
app.include_router(privilegio_api.router)

# Perfiles
app.include_router(cliente_api.router)
app.include_router(vehiculo_api.router)
app.include_router(taller_api.router)
app.include_router(servicio_taller_api.router)
app.include_router(tecnico_api.router)

# Emergencias
app.include_router(incidente_api.router)
app.include_router(evidencia_api.router)

# IA
app.include_router(ia_procesamiento_api.router)
app.include_router(ia_analisis_api.router)

# Talleres
app.include_router(orden_servicio_api.router)
app.include_router(asignacion_candidato_api.router)
app.include_router(cotizacion_api.router)
app.include_router(tenant_api.router)

# Pagos
app.include_router(detalle_orden_api.router)
app.include_router(transaccion_api.router)

# Analítica
app.include_router(kpi_router_api.router)
app.include_router(reporte_voz_api.router)

# Tracking WebSocket
app.include_router(tracking_router.router)


@app.get("/")
def read_root():
    return {"status": "Online", "message": "API de Emergencias Vehiculares lista"}
