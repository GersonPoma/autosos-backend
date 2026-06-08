from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    id_usuario: int
    id_perfil: int | None = None   # id_cliente o id_tecnico
    id_taller: int | None = None   # para admin_taller y tecnico
    tenant_id: int | None = None
    rol: str
    super_usuario: bool = False
    privilegios: list[str] = []


class UsuarioCrear(BaseModel):
    username: str
    password: str
    rol_id: int | None = None
    tenant_id: int | None = None
    super_usuario: bool = False


class UsuarioActualizar(BaseModel):
    username: str | None = None
    password: str | None = None
    rol_id: int | None = None


class UsuarioSalida(BaseModel):
    id: int
    username: str
    rol_id: int | None = None
    rol_nombre: str | None = None
    super_usuario: bool = False

    class Config:
        from_attributes = True


class FcmTokenRegistrar(BaseModel):
    fcm_token: str