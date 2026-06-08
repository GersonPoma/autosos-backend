from pydantic import BaseModel


class AnalisisCrear(BaseModel):
    transcripcion_audio: str
    categoria_problema: str
    danios_identificados: str
    resumen_estructurado: str
    incidente_id: int


class AnalisisActualizar(BaseModel):
    transcripcion_audio: str | None = None
    categoria_problema: str | None = None
    danios_identificados: str | None = None
    resumen_estructurado: str | None = None


class AnalisisSalida(BaseModel):
    id: int
    transcripcion_audio: str
    categoria_problema: str
    danios_identificados: str
    resumen_estructurado: str
    incidente_id: int

    class Config:
        from_attributes = True

