# AutoSOS - Backend

Backend REST API para gestión de emergencias vehiculares en tiempo real. Construido con FastAPI, SQLAlchemy y PostgreSQL.

## Requisitos

- Python 3.10 o superior
- PostgreSQL

## Instalación

### 1. Clonar y entrar al proyecto

```powershell
git clone <URL_DEL_REPOSITORIO>
Set-Location "backend_emergencia_vehiculares"
```

### 2. Entorno virtual

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
```

> Si PowerShell bloquea scripts, ejecuta una vez:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y ajusta tus valores:

```powershell
Copy-Item .env.exampe .env
```

Edita `.env` con tus datos:

```dotenv
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=db_emergencias

SECRET_KEY=tu_clave_secreta
ALGORITHM=HS256
# ACCESS_TOKEN_EXPIRE_MINUTES=60   (1 hora)
ACCESS_TOKEN_EXPIRE_MINUTES=10080  (7 días)
```

### 5. Levantar el servidor

Opcion A - Solo pruebas en esta misma PC (web local):

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Opcion B - Pruebas desde Flutter movil (emulador o celular en red local):

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

`0.0.0.0` permite que otros dispositivos de tu red local puedan conectarse al backend.

Al iniciar, el sistema automaticamente:
- Crea todas las tablas en la base de datos
- Ejecuta el seeder con los roles (`cliente`, `tecnico`, `admin_taller`) y privilegios del sistema

La API queda disponible en:
- `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`

### Pruebas locales desde Flutter movil

Si usas la opcion B (`--host 0.0.0.0`), en Flutter usa esta `baseUrl` segun el entorno:

- Android emulator: `http://10.0.2.2:8000`
- iOS simulator: `http://127.0.0.1:8000`
- Celular fisico: `http://<IP_DE_TU_PC>:8000` (ejemplo: `http://192.168.1.50:8000`)

---

## Estructura del proyecto

```
app/
├── api/
│   ├── cuentas/        # auth, roles, usuarios, privilegios
│   └── perfiles/       # clientes, vehiculos, talleres, servicios, tecnicos
├── core/
│   ├── base_model.py   # Mixin SoftDelete (created_at, updated_at, deleted, deleted_at)
│   ├── paginacion.py   # Schema generico de paginacion
│   └── security.py     # JWT, hashing, autenticacion
├── db/
│   ├── session.py      # Conexion SQLAlchemy
│   └── seeder.py       # Datos iniciales (roles y privilegios)
├── models/
│   ├── cuentas/        # Rol, Usuario, Privilegio, RolPrivilegio
│   └── perfiles/       # Cliente, Vehiculo, Taller, ServicioTaller, Tecnico
├── schemas/
│   ├── cuentas/        # Schemas de autenticacion y usuarios
│   └── perfiles/       # Schemas de perfiles
├── services/
│   ├── cuentas/        # Logica de negocio de cuentas
│   └── perfiles/       # Logica de negocio de perfiles
└── main.py
```

---

## Autenticación

Todas las rutas excepto las de registro y login requieren token JWT.

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "username": "usuario",
  "password": "contrasena"
}
```

Respuesta:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "id_usuario": 1,
  "id_perfil": 3,
  "id_taller": null,
  "rol": "cliente",
  "privilegios": []
}
```

Para usar el token en Swagger, haz clic en **Authorize** y pega el `access_token`.

---

## Endpoints principales

### Publicos (sin token)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/auth/login` | Iniciar sesión |
| `POST` | `/clientes/registrar` | Registrar cliente |
| `POST` | `/talleres/registrar` | Registrar taller |

### Protegidos (requieren token)

| Módulo | Prefijo |
|--------|---------|
| Roles | `/roles` |
| Usuarios | `/usuarios` |
| Privilegios | `/privilegios` |
| Clientes | `/clientes` |
| Vehículos | `/vehiculos` |
| Talleres | `/talleres` |
| Servicios del taller | `/servicios-taller` |
| Técnicos | `/tecnicos` |

---

## Paginación

Los endpoints de listado devuelven:

```json
{
  "datos": [...],
  "total": 15,
  "pagina": 1,
  "limite": 10,
  "total_paginas": 2
}
```

Parámetros query: `?pagina=1&limite=10`
