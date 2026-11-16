# Rendimiento de las recomendaciones

Verificación local: 12 de noviembre de 2026, America/Bogota.

## Resultado

La comparación consecutiva de la versión anterior y la optimizada redujo el tiempo de las 10.000 solicitudes de **44,21 a 21,16 segundos (52,12 %)**, con **0 errores** en ambas versiones. El promedio por respuesta bajó de **216,23 a 102,59 ms**, y el percentil 95 de **264,99 a 129,78 ms**.

Todos los tiempos de la tabla son **antes → después**. El tiempo de lote mide cuándo terminaron todas las peticiones; la latencia mide cada respuesta HTTP completa.

| Solicitudes | Lote (s) | Promedio (ms) | p95 (ms) | Solicitudes/s | Reducción del lote |
| --- | --- | --- | --- | --- | --- |
| 300 | 1.32 → 0.66 | 211.43 → 106.15 | 251.49 → 169.08 | 226.78 → 451.97 | 49.82% |
| 10,000 | 44.21 → 21.16 | 216.23 → 102.59 | 264.99 → 129.78 | 226.21 → 472.49 | 52.12% |

El p99 de las 10.000 peticiones bajó de 292,32 a 153,70 ms. El máximo aislado pasó de 355,63 a 589,80 ms; la mejora del promedio y los percentiles no garantiza que cada petición individual sea más rápida. Es una comparación de dos ejecuciones consecutivas en un equipo compartido, sin intervalos de confianza estadísticos.

La medición inicial, realizada antes de estas optimizaciones, había dado 40,23 s para 10.000 solicitudes. Volver a medir la versión anterior dio 44,21 s: la carga del equipo introduce variación. Por eso la tabla usa la pareja consecutiva registrada con el mismo generador. Durante el desarrollo, otras mediciones de la versión final dieron 26,01 s; se conservan como exploración local y no se mezclan con esta pareja.

## Cambios aplicados

1. **Una lectura de Neo4j por ranking.** Antes se consultaba primero la entidad y después sus coincidencias en dos transacciones. `MatchingRepository` obtiene ambos en una consulta gestionada, deduplica vecinos con `collect(DISTINCT ...)` y distingue una entidad inexistente de una entidad sin coincidencias. Se aplica a recomendaciones de vacantes y de candidatos.
2. **Menos cambios de hilo.** Las dependencias que solo validan la clave o construyen objetos se resuelven de forma asíncrona, sin enviarlas individualmente al pool de hilos. Las consultas bloqueantes permanecen en las rutas síncronas ejecutadas en un hilo de trabajo. El driver se inicializa y verifica durante el arranque.
3. **Registro HTTP mediante ASGI.** Se elimina el puente de tareas y streams de `BaseHTTPMiddleware`. Se mantienen el ID por petición, las cabeceras, el registro de la plantilla de ruta, el manejo seguro de errores y el envío progresivo de contenido.

Un perfil de 100 llamadas directas al servicio atribuyó aproximadamente el 85 % del tiempo a las dos lecturas gestionadas de Neo4j. Unificar solo la consulta dio 30,48 s para las 10.000 peticiones en una prueba exploratoria. Las demás optimizaciones reducen el trabajo HTTP que ese perfil del servicio no incluía.

Las respuestas se calculan con datos actuales: **no hay caché de recomendaciones**. Se mantienen pesos, fórmula, filtros, orden de desempate, autenticación, trazas para la máquina y registro de solicitudes. El HTML original de vacantes conserva su SHA-256.

## Método y entorno

- GET `/api/v1/candidates/c-202/recommendations?limit=10&minScore=0` contra `http://127.0.0.1:18000`.
- **50 peticiones activas en total**, repartidas en cuatro procesos generadores: 13, 13, 12 y 12. Modelo cerrado: cada cliente envía otra petición cuando termina la anterior; HTTP/1.1 persistente y sin reintentos.
- Lotes de 300 y 10.000 peticiones, con 100 peticiones de calentamiento excluidas por lote. El cronómetro de lote empieza después de la barrera entre clientes y termina con el último cliente; no incluye arranque de procesos ni exportación de resultados.
- Cada respuesta debe ser HTTP 200 y cumplir el contrato de recomendaciones; se verificaron 300 y 10.000 IDs únicos de petición respectivamente. Cada consulta devolvió 8 recomendaciones.
- Base real Neo4j 5.26.12 Community: **11 candidatos y 12 vacantes**. Se conservó el mismo volumen. Las huellas de las respuestas en ambos sentidos del ranking coinciden antes y después.
- FastAPI/Uvicorn: **un worker**, registro y visor activados. API Key local vacía, igual en ambos casos; la autenticación configurada sigue cubierta por pruebas.
- Windows y Docker/WSL2 en el mismo equipo: 28 procesadores lógicos, 31,72 GiB de RAM; Docker ve 28 CPU y 15,48 GiB.
- La carga repite un candidato en una base pequeña y caliente. **10.000 solicitudes totales no equivalen a 10.000 usuarios simultáneos**. Este resultado no determina la capacidad de una base grande ni de un despliegue remoto.

Código anterior: `a70be328f1618a6a4b42d814aa01e5b53b930760`. Código de la optimización: `c31157ba1286eb353d0f9f08678b2203eda6d5bf`. [Resultados completos y huellas](performance/2026-11-12.json) incluyen las imágenes desplegadas, los tiempos sin redondeo de presentación, los percentiles y las huellas de los CSV de evidencia.

## Repetir la medición

Con la API y Neo4j saludables, Python 3.13 y las dependencias de `requirements.txt` instaladas, ejecutar desde la raíz del repositorio:

```powershell
python tools/benchmark_recommendations.py --base-url http://127.0.0.1:18000 --candidate c-202 --output ../medicion-nueva
```

El candidato debe existir. La herramienta solo realiza lecturas; no siembra ni modifica la base. `c-202` corresponde a los datos de esta verificación. Usa otro ID existente si tu base es distinta. Lee `API_KEY` del entorno o del `.env` sin escribirla en los resultados. Usa el puerto de tu despliegue; el predeterminado es 8000.

La carpeta de salida debe ser nueva. Guarda `resultados.json`, un CSV de latencias por caso y los resultados crudos de cada proceso. `--api-revision` permite registrar explícitamente la revisión que se está sirviendo: el commit del generador no identifica por sí solo el contenedor desplegado. Compara siempre con la misma base, concurrencia, configuración y generador; si los clientes alcanzan su límite de CPU, el resultado mide también ese límite.

## Validación funcional

- **121 pruebas aprobadas** con Neo4j real dentro del contenedor de la API: 1,28 s.
- Se comprueba actualización inmediata de ambos rankings, sin resultados obsoletos después de modificar habilidades; casos vacíos y 404 conservados.
- Pruebas de streaming: entrega de fragmentos sin retención y sin intentar reemplazar una respuesta ya iniciada.
- Ambas suites de navegador pasaron en Edge: persistencia real de perfiles y vacantes, errores 422, HTML original intacto, trazas sin claves, móvil y movimiento reducido; MP4 automático a 2×, espera y salida solo después de confirmar éxito.
- Tras la comparación, la imagen optimizada quedó activa y ambos contenedores saludables.
