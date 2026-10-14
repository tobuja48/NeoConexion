# NeoConexión

API de compatibilidad laboral construida con FastAPI, Python 3.12/3.13 y Neo4j. Registra candidatos y vacantes, busca ofertas y explica su compatibilidad mediante reglas deterministas.

## ¿Qué resuelve?

NeoConexión ayuda a comparar perfiles laborales con los requisitos de una oferta. Una empresa puede consultar un ranking de candidatos y un candidato puede encontrar vacantes o conocer las habilidades que le faltan para un cargo específico.

- Registro y actualización de candidatos, experiencia, ubicación y habilidades.
- Publicación de vacantes con requisitos obligatorios y deseables.
- Búsqueda de ofertas por texto, ciudad y modalidad, con paginación.
- Recomendaciones en ambas direcciones con puntuación y explicación.
- Diagnóstico directo de habilidades faltantes, incluso sin coincidencias en el ranking.
- Documentación interactiva de la API y manual HTML con simulador.

## Contenido

- [Tecnologías](#tecnologías)
- [Instalación con Docker](#arranque-con-docker)
- [Configuración](#configuración)
- [Desarrollo y pruebas](#desarrollo-y-pruebas)
- [Operaciones de la API](#operaciones)
- [Primera demostración](#primera-demostración-en-swagger)
- [Arquitectura](#arquitectura)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Solución de problemas](#solución-de-problemas)
- [Límites y seguridad](#límites-y-seguridad)

## Tecnologías

| Tecnología | Función en el proyecto |
| --- | --- |
| Python 3.12/3.13 | Lenguaje del backend y del algoritmo de compatibilidad |
| FastAPI | Rutas HTTP, inyección de dependencias y contrato OpenAPI |
| Pydantic y pydantic-settings | Validación de datos y configuración del entorno |
| Neo4j y driver oficial | Persistencia de nodos, relaciones y consultas Cypher |
| Uvicorn | Servidor ASGI que ejecuta la API |
| Docker Compose | Arranque de la API y Neo4j con red, volumen y healthchecks |
| pytest y HTTPX | Pruebas unitarias, contratos HTTP e integración |
| HTML, CSS y JavaScript | Manual de exposición y simulador local |

Las versiones de las dependencias Python están fijadas en [requirements.txt](requirements.txt). Neo4j utiliza la imagen definida en [docker-compose.yml](docker-compose.yml).

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

## Configuración

Copia [.env.example](.env.example) a `.env` y ajusta sus valores antes del primer arranque.

| Variable | Uso |
| --- | --- |
| `NEO4J_URI` | Conexión Bolt para ejecución local; Compose configura la dirección interna de la API |
| `NEO4J_USER` | Usuario de la base de datos |
| `NEO4J_PASSWORD` | Contraseña de Neo4j; sustituye el valor de desarrollo del ejemplo |
| `API_KEY` | Clave opcional enviada mediante la cabecera `X-API-Key` |
| `LOG_LEVEL` | Nivel de registro, por ejemplo `INFO` |
| `API_PORT` | Puerto del host para la API; predeterminado `8000` |
| `NEO4J_HTTP_PORT` | Puerto del host para Neo4j Browser; predeterminado `7474` |
| `NEO4J_BOLT_PORT` | Puerto del host para Bolt; predeterminado `7687` |

El archivo `.env` está excluido de Git. En Linux o macOS, usa `cp .env.example .env` en lugar de `Copy-Item`.

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

## Primera demostración en Swagger

1. Abre `/docs` en la dirección donde corre la API. Si configuraste `API_KEY`, pulsa **Authorize** e introduce la clave.
2. Abre `POST /api/v1/candidates`, pulsa **Try it out** y registra este candidato:

```json
{
  "id": "demo-candidato",
  "name": "Ana Pérez",
  "location": "Bogotá",
  "yearsOfExperience": 3,
  "skills": ["Python", "Docker"],
  "preferredWorkMode": "remote"
}
```

3. En `POST /api/v1/jobs`, registra esta vacante:

```json
{
  "id": "demo-vacante",
  "company": "Empresa de ejemplo",
  "title": "Desarrollador Backend",
  "location": "Bogotá",
  "workMode": "remote",
  "requiredExperience": 3,
  "requiredSkills": ["Python", "SQL"],
  "desiredSkills": ["Docker"]
}
```

4. Consulta `GET /api/v1/jobs/demo-vacante/candidates` para ver el ranking.
5. Consulta `GET /api/v1/candidates/demo-candidato/jobs/demo-vacante/diagnosis` para ver la comparación directa.

En este ejemplo, falta **SQL**. El componente de habilidades vale **65**, los otros tres componentes valen **100** y la puntuación total es **82.5/100**. El candidato pasa el prefiltro porque comparte Python y Docker. Repetir los POST con esos IDs actualiza los ejemplos existentes.

Swagger envía solicitudes reales y guarda los datos de los POST. El simulador de [documentacion.html](documentacion.html) funciona en el navegador y no modifica Neo4j. GitHub muestra el código del HTML: descarga el repositorio y abre ese archivo en un navegador para utilizarlo.

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

## Estructura del proyecto

```text
NeoConexion/
├── app/
│   ├── api/v1/           # Endpoints y router versionado
│   ├── core/             # Configuración, errores, logs y driver
│   ├── domain/matching/  # Reglas puras y cálculo de compatibilidad
│   ├── repositories/     # Persistencia y consultas Cypher
│   ├── schemas/          # Contratos de entrada y salida
│   ├── services/         # Casos de uso
│   └── main.py           # Aplicación y ciclo de vida
├── tests/
│   ├── unit/             # Reglas, validaciones y contratos
│   └── integration/      # Operaciones con Neo4j real
├── docs/                 # Historias y registro de PRs
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requests.sh           # Recorrido de ejemplo con curl
├── documentacion.html    # Manual interactivo
└── VERIFICATION.md       # Evidencia de pruebas
```

La última verificación registrada incluye **98 pruebas aprobadas**. Consulta [VERIFICATION.md](VERIFICATION.md) para conocer el entorno y los límites de esa comprobación.

## Solución de problemas

| Problema | Qué comprobar |
| --- | --- |
| El navegador muestra “Connection refused” | Enciende Docker Desktop y ejecuta `docker compose up -d --wait`; comprueba el puerto configurado en `.env` |
| Un puerto está ocupado | Ajusta los puertos del host en `.env` y usa las nuevas direcciones; para Python local, ajusta también `NEO4J_URI` |
| La API no puede conectar con Neo4j | Revisa `docker compose ps` y `docker compose logs --tail 50 api neo4j`; comprueba las credenciales |
| Respuesta 401 | Envía la clave configurada en `API_KEY` mediante `X-API-Key` o **Authorize** en Swagger |
| Respuesta 422 | Revisa los campos, modalidades y valores indicados en el error; no se admiten campos extra |
| Ranking vacío | Comprueba habilidades compartidas y `minScore`; usa diagnóstico directo para analizar un par excluido |
| Cambié la contraseña pero no puedo entrar | El volumen conserva la base existente; cambiar `.env` no cambia la contraseña guardada en Neo4j |

## Límites y seguridad

No hay portal de usuarios, postulaciones, roles, correos, n8n, IA generativa, feedback persistido, aprendizaje de pesos, CI/CD ni pruebas de carga. Los rankings puntúan en memoria todos los candidatos prefiltrados. La normalización no unifica sinónimos ni acentos; los catálogos huérfanos pueden acumularse. Los logs propios usan identificadores de solicitud y evitan cuerpos y claves.

Los puertos de Compose se enlazan a 127.0.0.1. No publiques `.env`. Los datos de pruebas usan prefijos aleatorios y se limpian sin borrar datos ajenos. Para una exposición, Swagger muestra solicitudes reales y el HTML ofrece una simulación didáctica que no escribe en la base.
