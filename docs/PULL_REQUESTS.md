# Índice de los 40 pull requests

Cada PR se basa en la rama anterior y contiene su incremento. **No se ha fusionado ningún PR automáticamente.** La rama `rebuild/40-delivery-guide` contiene la versión completa.

| Orden | Pull request | Cambio | Rama | Historias relacionadas |
| --- | --- | --- | --- | --- |
| 01 | [#25](https://github.com/tobuja48/NeoConexion/pull/25) | Inicializar estructura Python y dependencias reproducibles | `rebuild/01-foundation` | Infraestructura/documentación |
| 02 | [#26](https://github.com/tobuja48/NeoConexion/pull/26) | Configurar variables de entorno y secretos | `rebuild/02-settings` | Infraestructura/documentación |
| 03 | [#27](https://github.com/tobuja48/NeoConexion/pull/27) | Normalizar claves y deduplicar habilidades | `rebuild/03-normalization` | #1, #7 |
| 04 | [#28](https://github.com/tobuja48/NeoConexion/pull/28) | Definir entidades de dominio y resultado de compatibilidad | `rebuild/04-domain-models` | #7 |
| 05 | [#29](https://github.com/tobuja48/NeoConexion/pull/29) | Validar pesos configurables del algoritmo | `rebuild/05-weights` | #8 |
| 06 | [#30](https://github.com/tobuja48/NeoConexion/pull/30) | Calcular cobertura de habilidades obligatorias y deseables | `rebuild/06-skill-coverage` | #8, #19 |
| 07 | [#31](https://github.com/tobuja48/NeoConexion/pull/31) | Calcular compatibilidad por experiencia | `rebuild/07-experience` | #8 |
| 08 | [#32](https://github.com/tobuja48/NeoConexion/pull/32) | Calcular ubicación y modalidad compatibles | `rebuild/08-work-preferences` | #8 |
| 09 | [#33](https://github.com/tobuja48/NeoConexion/pull/33) | Integrar scoring interpretable y explicaciones en español | `rebuild/09-matching-engine` | #8, #19 |
| 10 | [#34](https://github.com/tobuja48/NeoConexion/pull/34) | Definir tipos públicos, modalidades y formato de error | `rebuild/10-public-contract` | Infraestructura/documentación |
| 11 | [#35](https://github.com/tobuja48/NeoConexion/pull/35) | Validar registro y habilidades de candidatos | `rebuild/11-candidate-schema` | #1 |
| 12 | [#36](https://github.com/tobuja48/NeoConexion/pull/36) | Validar requisitos obligatorios y deseables de vacantes | `rebuild/12-job-schema` | #4 |
| 13 | [#37](https://github.com/tobuja48/NeoConexion/pull/37) | Gestionar driver Neo4j compartido y cierre de recursos | `rebuild/13-driver` | #7 |
| 14 | [#38](https://github.com/tobuja48/NeoConexion/pull/38) | Crear constraints idempotentes del grafo | `rebuild/14-constraints` | #7 |
| 15 | [#39](https://github.com/tobuja48/NeoConexion/pull/39) | Implementar proyecciones y MERGE transaccional | `rebuild/15-graph-primitives` | #7 |
| 16 | [#40](https://github.com/tobuja48/NeoConexion/pull/40) | Persistir candidatos y reemplazar relaciones atómicamente | `rebuild/16-candidate-repository` | #1, #7 |
| 17 | [#41](https://github.com/tobuja48/NeoConexion/pull/41) | Persistir vacantes, empresas y requisitos | `rebuild/17-job-repository` | #4, #7 |
| 18 | [#42](https://github.com/tobuja48/NeoConexion/pull/42) | Unificar errores HTTP y ocultar detalles internos | `rebuild/18-error-handlers` | Infraestructura/documentación |
| 19 | [#43](https://github.com/tobuja48/NeoConexion/pull/43) | Registrar solicitudes con identificadores y sin datos sensibles | `rebuild/19-request-logging` | #14 |
| 20 | [#44](https://github.com/tobuja48/NeoConexion/pull/44) | Coordinar alta y consulta de candidatos | `rebuild/20-candidate-service` | #1 |
| 21 | [#45](https://github.com/tobuja48/NeoConexion/pull/45) | Coordinar publicación y consulta de vacantes | `rebuild/21-job-service` | #4 |
| 22 | [#46](https://github.com/tobuja48/NeoConexion/pull/46) | Ordenar recomendaciones y aplicar umbral y límite | `rebuild/22-ranking-service` | #8 |
| 23 | [#47](https://github.com/tobuja48/NeoConexion/pull/47) | Exponer desglose y explicaciones del ranking | `rebuild/23-recommendation-contract` | #8, #19 |
| 24 | [#48](https://github.com/tobuja48/NeoConexion/pull/48) | Inyectar servicios y proteger rutas con API Key opcional | `rebuild/24-dependencies` | Infraestructura/documentación |
| 25 | [#49](https://github.com/tobuja48/NeoConexion/pull/49) | Exponer POST y GET de candidatos | `rebuild/25-candidate-endpoints` | #1 |
| 26 | [#50](https://github.com/tobuja48/NeoConexion/pull/50) | Exponer publicación y consulta de vacantes | `rebuild/26-job-endpoints` | #4 |
| 27 | [#51](https://github.com/tobuja48/NeoConexion/pull/51) | Exponer recomendaciones en ambas direcciones | `rebuild/27-recommendation-endpoints` | #8 |
| 28 | [#52](https://github.com/tobuja48/NeoConexion/pull/52) | Ensamblar API versionada, lifespan y OpenAPI | `rebuild/28-application` | Infraestructura/documentación |
| 29 | [#53](https://github.com/tobuja48/NeoConexion/pull/53) | Verificar disponibilidad y errores de salud | `rebuild/29-health` | Infraestructura/documentación |
| 30 | [#54](https://github.com/tobuja48/NeoConexion/pull/54) | Verificar registro idempotente y validaciones de candidatos | `rebuild/30-candidate-integration` | #1 |
| 31 | [#55](https://github.com/tobuja48/NeoConexion/pull/55) | Verificar publicación de requisitos y actualización de vacantes | `rebuild/31-job-integration` | #4, #7 |
| 32 | [#56](https://github.com/tobuja48/NeoConexion/pull/56) | Verificar ranking masivo determinista y filtros | `rebuild/32-ranking-integration` | #8 |
| 33 | [#57](https://github.com/tobuja48/NeoConexion/pull/57) | Verificar concurrencia, rollback y constraints del grafo | `rebuild/33-transaction-integrity` | #7 |
| 34 | [#58](https://github.com/tobuja48/NeoConexion/pull/58) | Agregar búsqueda y filtros del catálogo de ofertas | `rebuild/34-job-catalog` | #5 |
| 35 | [#59](https://github.com/tobuja48/NeoConexion/pull/59) | Diagnosticar brechas entre cualquier candidato y vacante | `rebuild/35-skill-diagnosis` | #19 |
| 36 | [#60](https://github.com/tobuja48/NeoConexion/pull/60) | Definir despliegue Neo4j con volumen y healthcheck | `rebuild/36-neo4j-compose` | #7 |
| 37 | [#61](https://github.com/tobuja48/NeoConexion/pull/61) | Contenerizar la API con usuario no root y espera de Neo4j | `rebuild/37-api-container` | Infraestructura/documentación |
| 38 | [#62](https://github.com/tobuja48/NeoConexion/pull/62) | Documentar recorrido reproducible con solicitudes curl | `rebuild/38-http-examples` | #1, #4, #8 |
| 39 | [#63](https://github.com/tobuja48/NeoConexion/pull/63) | Agregar guía técnica HTML con simulador de matching | `rebuild/39-html-manual` | Infraestructura/documentación |
| 40 | [#64](https://github.com/tobuja48/NeoConexion/pull/64) | Documentar ejecución, pruebas y trazabilidad de historias | `rebuild/40-delivery-guide` | Infraestructura/documentación |

## Cómo revisar e integrar

1. Revisa el PR 01 contra main y los siguientes contra la rama anterior. Los primeros incrementos aún no forman una aplicación ejecutable; cada PR declara las validaciones realizadas.
2. Integra en orden ascendente. Para conservar la ascendencia de esta cadena, usa merge commits, evitando squash/rebase de las ramas intermedias.
3. Después de integrar una rama, cambia la base del siguiente PR a main antes de integrarlo. No borres una rama que todavía sea base de otro PR. GitHub puede actualizar bases automáticamente, pero compruébalo.
4. Al terminar, ejecuta la suite completa y Docker Compose desde main. Solo entonces trata main como la entrega completa.

Los PRs que cubren historias incluyen referencias de cierre para que GitHub las procese cuando se integren en la rama predeterminada. No se cerraron issues solo por crear los PRs.
