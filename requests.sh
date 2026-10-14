#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
headers=(-H 'Content-Type: application/json')
if [[ -n "${API_KEY:-}" ]]; then
  headers+=(-H "X-API-Key: ${API_KEY}")
fi

curl --fail-with-body -sS -i "${headers[@]}" -X POST "$BASE_URL/api/v1/candidates" \
  --data-binary @- <<'JSON'
{"id":"c-123","name":"Ana Pérez","location":"Bogotá","yearsOfExperience":5,"skills":["Python","Docker"],"preferredWorkMode":"remote","expectedSalary":5000000}
JSON
printf '\n'
curl --fail-with-body -sS -i "${headers[@]}" -X POST "$BASE_URL/api/v1/jobs" \
  --data-binary @- <<'JSON'
{"id":"j-456","company":"ACME","title":"Desarrollador Backend","description":"API en Python","location":"Bogotá","workMode":"remote","requiredExperience":3,"requiredSkills":["Python"],"desiredSkills":["Docker"]}
JSON
printf '\n'
curl --fail-with-body -sS "${headers[@]}" "$BASE_URL/api/v1/candidates/c-123"
printf '\n'
curl --fail-with-body -sS "${headers[@]}" "$BASE_URL/api/v1/jobs/j-456"
printf '\n'
curl --fail-with-body -sS "${headers[@]}" "$BASE_URL/api/v1/candidates/c-123/recommendations?limit=10&minScore=0"
printf '\n'
curl --fail-with-body -sS "${headers[@]}" "$BASE_URL/api/v1/jobs/j-456/candidates?limit=10&minScore=0"
printf '\n'

# Search, filter and paginate offers (HU06).
curl --fail-with-body -sS "${headers[@]}" "$BASE_URL/api/v1/jobs?q=Backend&workMode=remote&limit=10&offset=0"
printf '\n'
# Direct skill gap diagnosis (HU26), including pairs absent from recommendations.
curl --fail-with-body -sS "${headers[@]}" "$BASE_URL/api/v1/candidates/c-123/jobs/j-456/diagnosis"
printf '\n'
