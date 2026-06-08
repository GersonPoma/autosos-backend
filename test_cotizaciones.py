import sys
import os

from app.models.cuentas import privilegio
from app.models.ia import analisis
from app.models.pagos import detalle_orden, transaccion
from app.models.perfiles import taller, servicio_taller, tecnico

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
import app.models.cuentas.rol  # noqa
import app.models.talleres.tenant  # noqa
from app.services.talleres.cotizacion_service import listar_por_incidente

INCIDENTE_ID = 1

db = SessionLocal()
try:
    cotizaciones = listar_por_incidente(db, INCIDENTE_ID)

    if not cotizaciones:
        print(f"No hay cotizaciones para el incidente {INCIDENTE_ID}")
    else:
        print(f"{len(cotizaciones)} cotización(es) encontrada(s) para el incidente {INCIDENTE_ID}:\n")
        for c in cotizaciones:
            print(f"  ID:                   {c.id}")
            print(f"  Estado:               {c.estado_cotizacion}")
            print(f"  Tipo atención:        {c.tipo_atencion}")
            print(f"  Distancia:            {c.distancia_km} km")
            print(f"  Tiempo estimado:      {c.tiempo_estimado_llegada} seg")
            print(f"  Costo total:          Bs. {c.costo_total}")
            print(f"  Fecha emisión:        {c.fecha_emision}")
            print(f"  Fecha validez:        {c.fecha_validez}")
            print(f"  Taller:               {c.asignacion_candidato.taller.nombre if c.asignacion_candidato and c.asignacion_candidato.taller else 'N/A'}")
            print(f"  Detalles:")
            for d in c.detalles:
                print(f"    - {d.servicio_taller.nombre if d.servicio_taller else 'N/A'} x{d.cantidad} @ Bs.{d.precio_unitario} = Bs.{d.subtotal}")
            print()
finally:
    db.close()