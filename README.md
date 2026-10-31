# Proyecto Iglesia

Sistema web monolítico para la gestión de una iglesia, construido con Django, SQLite, plantillas Bootstrap 5 y zona horaria `America/Merida`.

## Requisitos

- Windows 10/11.
- Python 3.13 o superior.
- PowerShell.
- SQLite, incluido con Python.

Las dependencias están fijadas en [requirements.txt](requirements.txt).

## Instalación en Windows

Desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `.env` y sustituye `SECRET_KEY` por una clave larga y aleatoria. El archivo `.env` no debe subirse al repositorio.

Inicializa la base:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py crear_administrador --correo admin@iglesia.local --nombre "Administrador" --contraseña "Usa-una-clave-segura"
```

Ejecuta el servidor:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Abre <http://127.0.0.1:8000/cuentas/login/>.

## Configuración de `.env`

En desarrollo usa:

```env
DEBUG=True
SECRET_KEY=una-clave-larga-y-secreta
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

En producción configura `DEBUG=False`, una `SECRET_KEY` obligatoria, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` con URLs HTTPS y las variables `EMAIL_*`. Activa HTTPS con `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True` y `CSRF_COOKIE_SECURE=True`.

La sesión expira después de dos horas de inactividad por defecto. Se puede ajustar con `SESSION_COOKIE_AGE`.

## Datos de demostración

Solo con `DEBUG=True`:

```powershell
.\.venv\Scripts\python.exe manage.py cargar_datos_demo
```

El comando es idempotente y no crea usuarios ni contraseñas.

## Pruebas y respaldo

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py check --deploy
.\.venv\Scripts\python.exe manage.py makemigrations --check
.\.venv\Scripts\python.exe manage.py test
```

Crea un respaldo SQLite consistente con la API de respaldo:

```powershell
.\.venv\Scripts\python.exe manage.py respaldar_bd
```

Los respaldos se guardan en `respaldos/` y se conservan los diez más recientes. Los errores de aplicación se registran en `logs/app.log` con rotación. Ambas carpetas están excluidas de Git.

El correo de recuperación se muestra en la terminal cuando `EMAIL_BACKEND` usa `django.core.mail.backends.console.EmailBackend`.

Para que las personas reciban el enlace en su correo, configura un servidor SMTP real en `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.tu-proveedor.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-cuenta@tu-dominio.com
EMAIL_HOST_PASSWORD=tu-contraseña-o-clave-de-aplicación
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=tu-cuenta@tu-dominio.com
```

La pantalla de recuperación muestra el mismo resultado para correos registrados y no registrados. Esto es intencional: evita que alguien descubra qué cuentas existen en el sistema.

## Estructura

- `accounts/`: usuarios, autenticación y roles.
- `members/`: miembros y comandos de gestión.
- `institution/`: configuración de la iglesia y horarios.
- `ministries/`: ministerios e integrantes.
- `events/`: eventos y calendario.
- `attendance/`: asistencia e historial.
- `finance/`: aportaciones y resúmenes financieros.
- `announcements/`: anuncios.
- `reports/`: reportes y exportaciones.
- `core/`: permisos, dashboard, middleware y servicios comunes.
- `templates/`: plantillas HTML.
- `static/`: tema CSS, favicon y recursos estáticos.

## Roles y permisos

| Rol | Acceso principal |
|---|---|
| Administrador | Administración, miembros, ministerios, eventos, asistencia, finanzas, anuncios y reportes |
| Pastor | Consulta de miembros, ministerios, eventos, asistencia, finanzas, anuncios y reportes |
| Secretario | Gestión de miembros, ministerios, eventos, asistencia y anuncios; sin finanzas |
| Tesorero | Consulta de miembros, eventos, finanzas y reportes de ingresos |
| Coordinador | Sus ministerios, sus miembros, sus eventos, asistencia de su alcance y reportes permitidos |

El servidor valida todos los permisos. El menú únicamente oculta opciones como cortesía.

## Requisitos funcionales

| RF | Estado | Pantalla principal | Prueba automática |
|---|---|---|---|
| RF-01 | Completo | `/cuentas/login/`, `/cuentas/usuarios/` | `accounts/tests.py` |
| RF-02 | Completo | `/miembros/` | `members/tests.py` |
| RF-03 | Completo | `/asistencia/registrar/` | `attendance/tests.py` |
| RF-04 | Completo | `/eventos/`, `/eventos/calendario/` | `events/tests.py` |
| RF-05 | Completo | `/ministerios/` | `ministries/tests.py` |
| RF-06 | Completo | `/finanzas/` | `finance/tests.py` |
| RF-07 | Completo | `/anuncios/` | `announcements/tests.py` |
| RF-08 | Completo | `/` | `reports/tests.py` y `announcements/tests.py` |
| RF-09 | Completo | `/reportes/` | `reports/tests.py` |
| RF-10 | Completo | `/institucion/` | `institution/tests.py` |

## Solución de problemas

- **Falta `SECRET_KEY` con `DEBUG=False`**: agrega una clave larga en `.env`.
- **`DisallowedHost`**: agrega el host a `ALLOWED_HOSTS`.
- **Error CSRF**: agrega el origen HTTPS completo a `CSRF_TRUSTED_ORIGINS`.
- **No carga el tema visual**: ejecuta el servidor desde la raíz y usa `Ctrl+F5`; `STATICFILES_DIRS` apunta a `static/`.
- **No llega el correo de recuperación**: en desarrollo revisa la terminal donde corre `runserver`.
- **No se pueden abrir exportaciones**: instala el entorno con `python -m pip install -r requirements.txt`.
- **El servidor redirige por HTTPS en local**: usa `SECURE_SSL_REDIRECT=False` y las cookies seguras en `False` únicamente durante desarrollo HTTP.
