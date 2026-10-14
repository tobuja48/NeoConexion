# Trazabilidad de historias

Revisión: 13 de octubre de 2026. Las historias se consultaron directamente en GitHub. “Cubierta en backend” describe el caso de uso de la API, accesible desde Swagger; no implica una interfaz final, cuentas o permisos. Los PRs de esta entrega están integrados en main; la cobertura se limita a las funciones descritas en esta tabla.

| Historia | Cobertura | Evidencia y alcance |
| --- | --- | --- |
| [#1](https://github.com/tobuja48/NeoConexion/issues/1) HU01 — Registro y carga de habilidades | Cubierta en backend | [PR #54](https://github.com/tobuja48/NeoConexion/pull/54) — Registro, normalización y upsert de perfil y habilidades; sin autenticación de usuarios. |
| [#2](https://github.com/tobuja48/NeoConexion/issues/2) HU02 — Perfil corporativo enriquecido | Pendiente | No implementada en esta entrega. |
| [#3](https://github.com/tobuja48/NeoConexion/issues/3) HU03 — Gestión de roles y permisos de seguridad | Pendiente | No implementada en esta entrega. |
| [#4](https://github.com/tobuja48/NeoConexion/issues/4) HU05 — Publicación de vacantes con requisitos obligatorios | Cubierta en backend | [PR #55](https://github.com/tobuja48/NeoConexion/pull/55) — Publicación y actualización de vacantes con requisitos obligatorios y deseables. |
| [#5](https://github.com/tobuja48/NeoConexion/issues/5) HU06 — Buscador y filtrado del catálogo de ofertas | Cubierta en backend | [PR #58](https://github.com/tobuja48/NeoConexion/pull/58) — Búsqueda textual, filtros de ciudad/modalidad y paginación de ofertas. |
| [#6](https://github.com/tobuja48/NeoConexion/issues/6) HU07 — Postulación rápida de un clic | Pendiente | No implementada en esta entrega. |
| [#7](https://github.com/tobuja48/NeoConexion/issues/7) HU09 — Modelado y almacenamiento en Neo4j | Cubierta en backend | [PR #57](https://github.com/tobuja48/NeoConexion/pull/57) — Nodos, relaciones, constraints, rollback y concurrencia verificados con Neo4j. |
| [#8](https://github.com/tobuja48/NeoConexion/issues/8) HU10 — Ranking masivo para reclutadores | Cubierta en backend | [PR #56](https://github.com/tobuja48/NeoConexion/pull/56) — Ranking de candidatos registrados; no existe todavía entidad de postulación. |
| [#9](https://github.com/tobuja48/NeoConexion/issues/9) HU11 — Explicación del match mediante IA | Pendiente | No implementada en esta entrega. |
| [#10](https://github.com/tobuja48/NeoConexion/issues/10) HU12 — Visualización gráfica de habilidades compartidas | Pendiente | No implementada en esta entrega. |
| [#11](https://github.com/tobuja48/NeoConexion/issues/11) HU15 — Correo con ranking diario | Pendiente | No implementada en esta entrega. |
| [#12](https://github.com/tobuja48/NeoConexion/issues/12) HU16 — Alertas de candidatos altamente compatibles | Pendiente | No implementada en esta entrega. |
| [#13](https://github.com/tobuja48/NeoConexion/issues/13) HU18 — Dashboard de métricas | Pendiente | No implementada en esta entrega. |
| [#14](https://github.com/tobuja48/NeoConexion/issues/14) HU19 — Monitorización y reportes | Parcial | Logs con request ID y endpoints de salud; faltan panel y reportes administrativos. |
| [#15](https://github.com/tobuja48/NeoConexion/issues/15) HU22 — Cambio del estado de una postulación | Pendiente | No implementada en esta entrega. |
| [#16](https://github.com/tobuja48/NeoConexion/issues/16) HU23 — Agendamiento de entrevistas | Pendiente | No implementada en esta entrega. |
| [#17](https://github.com/tobuja48/NeoConexion/issues/17) HU24 — Calificaciones y notas del reclutador | Pendiente | No implementada en esta entrega. |
| [#18](https://github.com/tobuja48/NeoConexion/issues/18) HU25 — Preguntas de entrevista generadas con IA | Pendiente | No implementada en esta entrega. |
| [#19](https://github.com/tobuja48/NeoConexion/issues/19) HU26 — Diagnóstico de habilidades faltantes | Cubierta en backend | [PR #59](https://github.com/tobuja48/NeoConexion/pull/59) — Diagnóstico de habilidades obligatorias faltantes para cualquier par existente. |
| [#20](https://github.com/tobuja48/NeoConexion/issues/20) HU27 — Ruta personalizada de aprendizaje | Pendiente | No implementada en esta entrega. |
| [#21](https://github.com/tobuja48/NeoConexion/issues/21) HU28 — Integración con plataformas educativas | Pendiente | No implementada en esta entrega. |
| [#22](https://github.com/tobuja48/NeoConexion/issues/22) HU29 — Correo con explicación del rechazo | Pendiente | No implementada en esta entrega. |
| [#23](https://github.com/tobuja48/NeoConexion/issues/23) HU30 — Evaluación de la precisión del matching | Pendiente | No implementada en esta entrega. |
| [#24](https://github.com/tobuja48/NeoConexion/issues/24) HU31 — Reajuste del algoritmo mediante retroalimentación | Pendiente | No implementada en esta entrega. |

Las explicaciones del motor no satisfacen la historia de explicación mediante IA (#9). El simulador HTML tampoco implementa visualización del grafo real (#10). Configurar pesos no satisface aprendizaje por feedback (#24). No se cerraron manualmente las historias.
