# Proyecto Iglesia

Sistema web monolÃ­tico para la gestiÃ³n de una iglesia, construido con Django y plantillas Bootstrap 5.

## Requisitos

- Python 3.13 o superior.
- SQLite (incluido con Python).

## InstalaciÃ³n

Desde esta carpeta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configura un archivo `.env` **fuera del repositorio**, en la carpeta padre `U2`:

```env
SECRET_KEY=una-clave-secreta
DEBUG=True
```

El proyecto carga esas variables automÃ¡ticamente. El correo de recuperaciÃ³n se muestra en la consola mediante el backend de correo de desarrollo.

### Dónde ver el correo de recuperación en desarrollo

Con `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` (valor predeterminado), el enlace de recuperación se imprime en la terminal donde ejecutas `python manage.py runserver`.

Para usar SMTP real, configura estas variables en el `.env` fuera del repositorio:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.ejemplo.com
EMAIL_PORT=587
EMAIL_HOST_USER=usuario-smtp
EMAIL_HOST_PASSWORD=contraseña-smtp
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=no-reply@iglesia.mx
```

## Puesta en marcha

```powershell
python manage.py migrate
python manage.py crear_administrador --correo admin@iglesia.mx --nombre "Administrador" --contraseÃ±a "cambia-esta-clave"
python manage.py runserver
```

Entra a `http://127.0.0.1:8000/cuentas/login/`.

## Pruebas

```powershell
python manage.py test
```

Los roles disponibles son Administrador, Pastor, Secretario, Tesorero y Coordinador. Cada usuario debe tener un solo grupo/rol; solo Administrador puede gestionar usuarios.
