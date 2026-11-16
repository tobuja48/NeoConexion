# Verificación de la reconstrucción

Fecha de verificación: 13 de octubre de 2026 (America/Bogota).

## Suite completa

```text
........................................................................ [ 73%]
..........................                                               [100%]
98 passed in 2.29s
```

**98 pruebas aprobadas** dentro de la imagen Python 3.13, con Neo4j 5.26.12 real en Docker. La suite contiene pruebas unitarias, contratos HTTP, autenticación opcional, validación, upserts, búsquedas, rankings, diagnóstico, concurrencia y rollback. No se omitieron pruebas por indisponibilidad de la base.

Comando: `docker compose -p neoconexion-rebuild exec -T api python -m pytest -q -x --tb=short -p no:cacheprovider`.

## Comprobaciones adicionales

- API y Neo4j arrancaron saludables con `docker compose up -d --build --wait`.
- Contenedor API ejecuta UID 10001; puertos de verificación 18000/17474/17687.
- `requests.sh` ejecutó altas, consultas, rankings, búsqueda y diagnóstico contra la API real.
- Manual renderizado en Edge: escritorio y móvil, sin errores JavaScript ni desbordamiento horizontal; controles y simulador comprobados.
- El manual HTML tiene anclas válidas y documenta las nuevas rutas comprobadas en OpenAPI.
- Todos los módulos Python de app y tests están versionados; `.env` está excluido.
- Cada incremento pasó sus verificaciones antes del push. Los resultados están en las descripciones de los PRs.

No son pruebas de carga ni certificación de producción. No se validaron portales, IA o n8n porque no están implementados. La API debe iniciarse con Docker Desktop disponible; un navegador con localhost no inicia servicios por sí mismo.

## Optimización de recomendaciones — 12 de noviembre de 2026

**121 pruebas aprobadas en 1,28 s** dentro del contenedor de la API, con Neo4j real. Además, ambas suites de `npm run test:browser` pasaron en Edge: app original, persistencia, validación, visor independiente, MP4 automático a 2×, estados de espera y salida confirmada, móvil y movimiento reducido.

La comparación consecutiva de 300 y 10.000 solicitudes entre la versión anterior y la optimizada mantuvo la misma base y 50 peticiones concurrentes. Las 10.000 terminaron en 44,21 s antes y 21,16 s después, sin errores. [Método, resultados y límites](docs/PERFORMANCE.md). Las respuestas comprobadas en ambos sentidos del ranking conservaron exactamente sus bytes; el HTML original mantuvo su SHA-256. Tras la prueba quedó activa la imagen optimizada.
