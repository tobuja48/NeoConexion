# Conecta Empleos · máquina JSON conectada

La app proporcionada se integró en `app/web/`. FastAPI la sirve en `/app/`, dentro de la misma imagen Docker y del mismo origen HTTP de la API. Esta versión usa únicamente solicitudes reales: se retiró el motor JavaScript embebido.

## Abrir y probar

1. Configura `.env` según el README y ejecuta `docker compose up -d --build --wait`.
2. Abre `http://localhost:8000/app/` o el puerto configurado en `API_PORT`. En el entorno local usado para esta entrega, la dirección es `http://127.0.0.1:18000/app/`.
3. Pulsa **Conectar / sincronizar API**. La URL inicial corresponde al servidor desde el que abriste la app. Si configuraste `API_KEY`, introdúcela aquí y pulsa **Probar conexión**.
4. Para trabajar con los ejemplos incluidos, pulsa **Sincronizar todos los datos**: son 11 vacantes y 10 candidatos. Se envían POST reales que crean o reemplazan registros por sus IDs. La app muestra cuántos fueron confirmados y cuántos fallaron.
5. Elige una sesión de candidato y entra en **Mi perfil**. Al escribir, la máquina muestra el JSON preparado. **Guardar perfil** envía el POST; la vista se desplaza a la máquina y muestra la respuesta real. Después puedes consultar recomendaciones o abrir una vacante para ver el diagnóstico.
6. Elige una empresa y entra en **Publicar vacante**. Completa los datos y publica: la salida HTTP refleja el registro guardado. El botón **Ver candidatos compatibles** realiza una consulta real de ranking y también queda en el historial de la máquina.

Los formularios de la plataforma incluyen campos propios, como título profesional, salario de la oferta y tipo de contrato. Los traductores solo envían a NeoConexión los campos admitidos por sus esquemas; el panel de entrada permite ver esa transformación.

## Qué significa la animación

| Estado | Evidencia real |
| --- | --- |
| Preparado | JSON generado a partir del formulario; todavía no se envió |
| Enviado / esperando | Fetch está pendiente y los engranajes giran |
| Respuesta HTTP | Se recibió el cuerpo del servidor, con su código y su X-Request-ID si está disponible |
| Error HTTP | La salida muestra el error real, por ejemplo una validación 422 |
| Sin confirmación | Hubo un error de red, CORS o timeout; no aparece un JSON de salida inventado |

La máquina representa el recorrido HTTP. No recibe telemetría de pasos internos de Neo4j ni inventa etapas de progreso. Una respuesta rápida puede completar el recorrido casi inmediatamente. Para recomendaciones, la salida es el cálculo real del backend; ese cálculo no crea un registro de ranking persistido.

Cada POST utiliza el mismo JSON que muestra la entrada. El formulario solo actualiza su copia local después de una respuesta exitosa. Si una respuesta se pierde después de que el servidor haya guardado, no se puede asegurar desde el navegador si hubo commit: la pantalla informa que falta confirmación y el reintento conserva el ID para permitir el upsert.

## Configuración y alcance

- Abierta en `/app/`, la app usa el mismo origen que la API y no requiere habilitar CORS. Para una API en otro origen, configura `CORS_ORIGINS` con el origen exacto del frontend. Una copia abierta por `file://` envía el origen `null` y necesita esa configuración en desarrollo.
- La API Key se envía en X-API-Key, se mantiene en sessionStorage de la pestaña y se excluye del historial visual. Es una herramienta local de prueba con clave compartida; el selector de sesiones no es autenticación de usuarios.
- El historial conserva hasta 40 solicitudes en memoria de la pestaña. Permite revisar la entrada y salida correspondientes sin confundir respuestas de solicitudes simultáneas. No persiste las respuestas en localStorage.
- Candidatos, vacantes, recomendaciones y diagnóstico usan la API. Empresas enriquecidas, salarios de ofertas, búsqueda local, postulaciones, invitaciones y cambios de estado siguen siendo datos de demostración del navegador.
- **Restaurar datos** restaura únicamente los ejemplos locales y no borra datos de Neo4j. La sincronización se realiza solo por acción explícita del usuario.
- Se respetan las preferencias de movimiento reducido. Los errores de red tienen un límite de espera de 20 segundos y no se sustituyen por resultados simulados.

## Verificación del navegador

La prueba requiere la API y Neo4j reales, Node.js 20 o superior, Docker Compose y Playwright. Desde la raíz del proyecto:

```powershell
npm ci
npx playwright install chromium
$env:BASE_URL = 'http://127.0.0.1:18000'
# Solo si la API está protegida:
# $env:API_KEY = 'tu-clave-local'
npm run test:browser
```

Para usar Edge ya instalado: `$env:BROWSER_CHANNEL = 'msedge'`. Si docker no está en PATH, establece `DOCKER_EXE` con la ruta de su ejecutable. El comando de limpieza asume que BASE_URL pertenece al servicio `api` de Docker Compose de este checkout; no lo apuntes a un despliegue ajeno. `SCREENSHOT_DIR` es opcional para guardar capturas.

La prueba crea fixtures con un prefijo UUID, comprueba un POST real y consulta el registro guardado antes de liberar la respuesta interceptada hacia el navegador. Mientras esa respuesta está retenida, exige que la máquina siga pendiente y sin salida JSON. Al liberarla, compara el JSON mostrado con el registro real. También verifica ranking, diagnóstico, publicación, actualización sin duplicados, errores 422 reales, fallos de transporte simulados, conteos de sincronización, historial, móvil y movimiento reducido. Al terminar elimina únicamente sus fixtures.

Las pruebas del backend continúan disponibles con `docker compose exec -T api python -m pytest -q -p no:cacheprovider`.
