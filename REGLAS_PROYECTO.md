# REGLAS DEL PROYECTO (leer completo antes de cualquier tarea)

## Producto
Sistema web de gestión para una iglesia. El entregable es software funcionando. Todo texto visible al usuario, mensajes y comentarios: español (es-mx). Apps existentes: core, accounts, members, institution. Apps por crear: ministries, events, attendance, finance, announcements, reports.

## Stack (no cambiar)
Django monolítico con plantillas, SQLite, Bootstrap 5 y JavaScript simple por CDN con versión fija. Sin API REST ni frontend separado. Zona horaria America/Merida. Entorno: Windows + PowerShell (no uses comandos exclusivos de Linux en scripts ni README). Dependencias nuevas solo si la tarea las autoriza; registrarlas en requirements.txt.

## Roles y permisos
Roles (grupos de Django): Administrador, Pastor, Secretario, Tesorero, Coordinador. Un usuario tiene un solo rol.
- Usuarios e Institución: solo Administrador.
- Miembros: Administrador y Secretario crean/editan/desactivan; Pastor y Tesorero solo ven; Coordinador solo ve miembros de los ministerios que coordina.
- Ministerios: Administrador, Pastor y Secretario gestionan; Coordinador ve solo los suyos; Tesorero sin acceso.
- Eventos y calendario: Administrador, Pastor y Secretario gestionan; Tesorero y Coordinador solo ven.
- Asistencia: Administrador, Pastor y Secretario registran y consultan todo; Coordinador solo eventos y miembros de sus ministerios; Tesorero sin acceso.
- Aportaciones (finanzas): Administrador y Tesorero gestionan; Pastor solo ve; Secretario y Coordinador sin acceso, ni en pantallas, ni en totales, ni en gráficas, ni en datos JSON, ni en exportaciones.
- Anuncios: Administrador, Pastor y Secretario gestionan; todos los roles autenticados los ven.
- Dashboard y reportes: se especifican en su etapa; la información financiera solo para Administrador, Pastor (solo ver) y Tesorero.

## Reglas de código y diseño
1. Los permisos se validan SIEMPRE en el servidor con el mixin/decorador centralizado de core/permissions.py. Ocultar botones es solo cortesía.
2. Usuario autenticado sin permiso: página 403 propia. Sin sesión: login de la app. Nunca enviar al usuario a /admin/ ni enlazarlo desde ningún menú.
3. Sin borrado físico en miembros, usuarios, ministerios, eventos ni aportaciones: se desactivan, cancelan o anulan. Excepciones: anuncios y filas de horarios sí se eliminan (con confirmación).
4. Toda acción que cambia datos (crear, editar, desactivar, cancelar, anular, eliminar, cerrar sesión) va por POST con CSRF; las destructivas o irreversibles piden confirmación previa (modal o página de confirmación).
5. Formularios: errores visibles por campo y generales (clase is-invalid), conservan lo escrito (excepto contraseñas), botón Cancelar, botón Volver en detalle y edición; al guardar con éxito redirigen al listado o detalle con mensaje de éxito (django.contrib.messages). Nunca dejar al usuario en el formulario tras guardar. Los widgets de fecha usan formato ISO para que se precarguen al editar.
6. Listados: paginados; búsqueda y filtros por GET que se conservan al paginar; botón "Limpiar filtros" siempre visible; estado vacío con mensaje claro.
7. Ningún flujo normal debe producir traceback: usar get_object_or_404, validar entradas y casos límite. Páginas 400/403/404/500 personalizadas en español.
8. Las páginas autenticadas llevan Cache-Control no-store (middleware existente).
9. Fechas dd/mm/aaaa; dinero con Decimal (nunca float) y formato "$1,234.50 MXN"; usar timezone.localdate() para "hoy".
10. Evitar consultas N+1 (select_related, prefetch_related, annotate) en listados y reportes.
11. Sin secretos en el código; configuración mediante .env.
12. Reutilizar lo existente (plantilla base, includes de formularios, mixins). La lógica de datos y cálculos va en services.py de cada app, devolviendo datos puros reutilizables.
13. No cambiar lo que ya funciona fuera del alcance de la tarea.

## Pruebas automáticas
Cada etapa agrega pruebas con el cliente de pruebas de Django para: permisos de cada ruta nueva por cada rol y sin sesión (GET y POST), validaciones, reglas de negocio y casos límite. Al terminar se ejecuta la suite COMPLETA y debe pasar. Si una prueba antigua falla por un cambio legítimo, corrígela y explícalo.

## Cierre de cada etapa (obligatorio)
1. Ejecutar python manage.py check, python manage.py makemigrations --check y la suite completa.
2. Commit con el mensaje indicado por la tarea (sin incluir media/, db.sqlite3, .env ni logs).
3. Reporte final con: (a) resumen de lo hecho, (b) decisiones tomadas donde algo era ambiguo, (c) problemas conocidos o pendientes, (d) LISTA DE PRUEBAS MANUALES.
La lista de pruebas manuales debe ser un checklist en español, agrupado por rol (Administrador, Pastor, Secretario, Tesorero, Coordinador y sin sesión), con las rutas reales, pasos concretos y resultado esperado; incluir casos de error (datos inválidos, permisos denegados, URLs pegadas a mano, ids inexistentes) y los comandos para tener datos de prueba. Debe estar redactada para alguien que NO ve el código y tener un máximo de 40 ítems, priorizando lo que más puede fallar.
Si algo es ambiguo, elige la opción más simple y razonable, anótala en (b) y continúa; pregunta solo si estás bloqueado.
