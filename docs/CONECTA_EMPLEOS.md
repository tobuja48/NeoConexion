# Vacantes originales y máquina JSON independiente

## Dos HTML separados

- `/app/` sirve `app/web/index.html`: una copia exacta, byte por byte, del archivo `conecta-empleos.html` entregado por el usuario. No se le insertan scripts, botones ni animaciones. SHA-256: `0177c4ba32f5d6e3acca56a23bbdd2d6b6814ab01d786698603e20bc29462126`.
- `/app/maquina.html` es el visor independiente. Sus recursos son `machine.js`, `machine.css` y `observer.js`. Observa la API desde otra pestaña, sin alterar el HTML de vacantes ni inyectar código en él.

FastAPI sirve ambas páginas desde la misma imagen Docker. La observación se hace en el servidor mediante middleware ASGI, conservando las respuestas y la validación de los endpoints originales.

## Demostración

1. Ejecuta `docker compose up -d --build --wait`.
2. Abre `/app/` en el puerto de la API. Por defecto es `http://localhost:8000/app/`; en el entorno de verificación se usa `http://127.0.0.1:18000/app/`.
3. En el pie de la app original, abre **Integración NeoConexión**. Selecciona **API NeoConexión por HTTP**, introduce el origen de esta API y, si corresponde, X-API-Key. Guarda la configuración y prueba la conexión. No añadas `/api/v1` ni `/docs` a la URL base.
4. Abre `/app/maquina.html` en otra pestaña del mismo servidor. Introduce la misma API Key si está configurada.
5. Desde la página original, guarda un perfil, publica una vacante o consulta compatibilidad. El visor se actualiza aproximadamente cada 700 ms y muestra la entrada y salida observadas en la API.
6. Para probar con todos los ejemplos, utiliza el botón de sincronización que ya existe en la página original: envía 11 vacantes y 10 candidatos mediante upserts reales por ID. Comprueba los resultados efectivos en el visor; la interfaz original conserva sus mensajes y su comportamiento tal como fue entregada.

La página original arranca por defecto con un motor embebido. Ese modo calcula en el navegador y no produce actividad en la API. Para la demostración de JSON reales debes elegir HTTP. Una copia abierta por doble clic requiere CORS para el origen `null`; abrirla desde `/app/` evita esa diferencia de origen.

## Evidencia y límites del visor

El endpoint `GET /api/v1/visualization/requests?after=0` devuelve registros temporales con un cursor de actualización. Está protegido por la misma dependencia X-API-Key que los endpoints de negocio y envía `Cache-Control: no-store`. La propia consulta del visor no se registra, evitando un bucle de observación.

El servidor conserva hasta 40 solicitudes GET o POST de candidatos y vacantes. No registra cabeceras de entrada ni API Keys. Los cuerpos se limitan a 128 KiB por entrada o respuesta; si superan ese límite se indica expresamente y no se presenta un fragmento como si fuera el JSON completo. Los registros existen solo en la memoria del proceso, se pierden al reiniciar y son compartidos entre quienes tienen acceso a esta API de prueba. Está pensado para una demostración local de un solo proceso, no como observabilidad multiusuario de producción.

| Situación | Qué muestra el visor |
| --- | --- |
| Solicitud observada y pendiente | Máquina trabajando, sin respuesta JSON todavía |
| Respuesta terminada | Código HTTP, JSON real, duración y X-Request-ID si existe |
| Error HTTP como 422 | Respuesta real de error, sin convertirla en un éxito |
| Solicitud muy rápida | Puede llegar ya completada en la siguiente actualización; no se inventa tiempo de procesamiento |
| Fallo de red antes de alcanzar la API | No hay registro: el servidor no recibió la solicitud |
| Visor sin conexión | Se informa la desconexión y no se inventan nuevas respuestas |

La respuesta mostrada corresponde a lo que el servidor produjo y envió. No demuestra que otro navegador ya la haya recibido o mostrado. Los registros del historial pueden describir operaciones anteriores y no son una consulta del estado actual de la base. Las recomendaciones se calculan en el backend; no se persiste un registro de ranking.

El visor no modifica los formularios ni corrige los mensajes optimistas, la búsqueda local o el almacenamiento de la página original. Empresas enriquecidas, sesiones de demostración, postulaciones e invitaciones conservan su implementación original en el navegador. El JSON de la máquina procede de las llamadas reales a la API.

La animación respeta movimiento reducido. Su historial visual vive en memoria de la pestaña y permite consultar solicitudes anteriores. La clave del visor se guarda en sessionStorage; la configuración de la página original permanece intacta.

## Pruebas

Backend y Neo4j real:

```powershell
docker compose exec -T api python -m pytest -q -p no:cacheprovider
```

Navegador, desde la raíz del checkout con Node.js 20 o superior:

```powershell
npm ci
npx playwright install chromium
$env:BASE_URL = 'http://127.0.0.1:18000'
# Solo si la API está protegida:
# $env:API_KEY = 'tu-clave-local'
npm run test:browser
```

Para Edge instalado: `$env:BROWSER_CHANNEL = 'msedge'`. Si docker no está en PATH, establece `DOCKER_EXE`. `SCREENSHOT_DIR` es opcional para guardar capturas. La prueba y su limpieza asumen que BASE_URL pertenece al servicio `api` de Docker Compose de este checkout; no la apuntes a otro despliegue.

La prueba verifica la huella exacta del HTML servido, abre las dos páginas, guarda desde el formulario original y compara lo mostrado en la máquina con un GET independiente del registro real. También comprueba publicación, errores 422, ausencia de registros inventados cuando la red falla antes de alcanzar la API, exclusión de claves, vista móvil y movimiento reducido. Solo elimina sus fixtures de prueba.

Verificación registrada de esta separación: 114 pruebas del backend aprobadas en Docker y prueba de navegador con las dos páginas aprobada.
