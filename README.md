# NeoConexión

API de compatibilidad laboral construida con FastAPI, Python 3.12/3.13 y Neo4j. Registra candidatos y vacantes, busca ofertas y explica su compatibilidad mediante reglas deterministas.

## Estado de la entrega

Reconstrucción sobre el repositorio inicial mediante **40 PRs encadenados**. La versión completa está integrada en `main`; los 40 PRs conservan el historial de cada incremento. Se reutilizaron módulos comprobados del prototipo local, se separaron las reglas del motor y se añadieron catálogo y diagnóstico directo. No es una reescritura íntegra de cada línea.

- [Índice de los 40 PRs](docs/PULL_REQUESTS.md): orden, alcance y ramas.
- [Historias y cobertura](docs/USER_STORIES.md): las 24 historias reales del repositorio.
- [Verificación reproducible](VERIFICATION.md): pruebas y límites comprobados.
- [Manual interactivo](documentacion.html): abrir el archivo en un navegador; no requiere servidor para el simulador.

## Arranque con Docker

Requisito: Docker Desktop encendido (WSL 2 en Windows) o Docker Engine con Compose.

```powershell
git clone --branch main https://github.com/tobuja48/NeoConexion.git
cd NeoConexion
Copy-Item .env.example .env
# Edita .env: establece NEO4J_USER=neo4j y una contraseña propia en NEO4J_PASSWORD.
# API_KEY vacía habilita acceso local sin autenticación; configura una clave si la necesitas.
docker compose up -d --build --wait
docker compose ps
```

No sobrescribas `.env` en arranques posteriores. Compose no necesita Python instalado en el host. La imagen utiliza Python 3.13 y usuario no root UID 10001.

| Recurso | Dirección predeterminada |
| --- | --- |
| Swagger | http://localhost:8000/docs |
| OpenAPI | http://localhost:8000/openapi.json |
| Salud del proceso / base | http://localhost:8000/health · http://localhost:8000/health/db |
| Neo4j Browser | http://localhost:7474 |
| Bolt | bolt://localhost:7687 |

`API_PORT`, `NEO4J_HTTP_PORT` y `NEO4J_BOLT_PORT` permiten coexistir con otro proyecto. Esta entrega se verificó con **18000, 17474 y 17687**, bajo el nombre Compose `neoconexion-rebuild`, conservando el prototipo anterior. Esos valores de verificación no cambian los valores predeterminados del repositorio.

La API dentro de Docker siempre usa `bolt://neo4j:7687`. Si ejecutas Python en el host con otro puerto Bolt, cambia también `NEO4J_URI` en `.env`. El volumen conserva los datos entre reinicios; cambiar la contraseña en `.env` no modifica automáticamente una base existente.

```powershell
docker compose logs --tail 50 api
docker compose restart api
docker compose stop
```

## Desarrollo y pruebas

```powershell
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
docker compose up -d --wait neo4j
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

Detén la API de Docker antes de usar el mismo puerto para Uvicorn. Las pruebas de integración requieren Neo4j real: fallan si no está disponible, no se omiten silenciosamente.

```powershell
docker compose exec api python -m pytest -q -p no:cacheprovider
# Alternativa local
.venv/Scripts/python.exe -m pytest tests/unit -q -p no:cacheprovider
.venv/Scripts/python.exe -m pytest tests/integration -q -p no:cacheprovider
```

`requests.sh` contiene un recorrido completo con curl para Git Bash/Linux/macOS. Crea o reemplaza los ejemplos `c-123` y `j-456`. Admite `BASE_URL` y `API_KEY`; no lee `.env` automáticamente.

```bash
BASE_URL=http://localhost:8000 bash requests.sh
```

## Operaciones

| Método | Ruta | Resultado |
| --- | --- | --- |
| POST | `/api/v1/candidates` | Crear (201) o reemplazar (200) candidato por ID |
| GET | `/api/v1/candidates/{id}` | Consultar candidato o 404 |
| POST | `/api/v1/jobs` | Crear (201) o reemplazar (200) vacante |
| GET | `/api/v1/jobs/{id}` | Consultar vacante o 404 |
| GET | `/api/v1/jobs` | Catálogo con q, location, workMode, limit y offset |
| GET | `/api/v1/candidates/{id}/recommendations` | Ranking de vacantes |
| GET | `/api/v1/jobs/{id}/candidates` | Ranking de candidatos registrados |
| GET | `/api/v1/candidates/{id}/jobs/{job_id}/diagnosis` | Diagnóstico directo de brechas |
| GET | `/health` | Estado del proceso |
| GET | `/health/db` | Conectividad Neo4j; 503 si no está disponible |

El catálogo busca texto en título, descripción o empresa sin distinguir mayúsculas. `location` compara una ciudad normalizada exacta; `workMode` acepta remote, hybrid u onsite. `limit` está entre 1 y 50; `offset` empieza en 0. Retorna `{total, limit, offset, items}` con orden estable por ID. El total y la página pueden cambiar si existen escrituras concurrentes.

Los rankings admiten `limit` (1–50) y `minScore` (0–100), ordenan por score descendente e ID ascendente y calculan `total` antes del límite. El prefiltro exige alguna habilidad compartida; diagnóstico compara cualquier par existente y devuelve `passesSkillPrefilter` además de `missingSkills`, `matchingSkills`, `breakdown`, `matchScore` y `explanations`.

Los contratos usan camelCase y rechazan campos desconocidos. POST reemplaza todo el recurso, no hace PATCH. X-API-Key solo se exige cuando API_KEY está configurada. No hay autorización por propietario.

## Arquitectura

```text
HTTP / Swagger
    → rutas y esquemas Pydantic
    → servicios de aplicación
    → repositorios → driver Neo4j → grafo
    → dominio puro de matching (sin HTTP ni consultas)
```

`app/api/` recibe solicitudes; `app/schemas/` valida el contrato; `app/services/` coordina casos de uso; `app/repositories/` concentra Cypher; `app/domain/matching/` puntúa; `app/core/` configura, registra y gestiona errores y conexiones. Las dependencias se inyectan desde FastAPI. Un driver se comparte durante el lifespan; las sesiones son por operación.

Nodos: Candidate, Job, Skill, Company, Location y WorkMode. Relaciones: HAS_SKILL, REQUIRES_SKILL, DESIRES_SKILL, POSTED, LIVES_IN, LOCATED_IN, PREFERS y OFFERS_MODE. Constraints únicos y transacciones de reemplazo evitan duplicados y cambios parciales.

Score = habilidades × 0.50 + experiencia × 0.25 + ubicación × 0.15 + modalidad × 0.10. Las obligatorias pesan 70% y las deseables 30% del componente de habilidades cuando ambas existen; sin deseables, las obligatorias pesan 100%. Sin obligatorias, ese componente vale 100. Experiencia se limita al 100%; remoto elimina penalización por ciudad. Las explicaciones son deterministas, no IA generativa. Salario no interviene en el score.

## Límites y seguridad

No hay portal de usuarios, postulaciones, roles, correos, n8n, IA generativa, feedback persistido, aprendizaje de pesos, CI/CD ni pruebas de carga. Los rankings puntúan en memoria todos los candidatos prefiltrados. La normalización no unifica sinónimos ni acentos; los catálogos huérfanos pueden acumularse. Los logs propios usan identificadores de solicitud y evitan cuerpos y claves.

Los puertos de Compose se enlazan a 127.0.0.1. No publiques `.env`. Los datos de pruebas usan prefijos aleatorios y se limpian sin borrar datos ajenos. Para una exposición, Swagger muestra solicitudes reales y el HTML ofrece una simulación didáctica que no escribe en la base.
