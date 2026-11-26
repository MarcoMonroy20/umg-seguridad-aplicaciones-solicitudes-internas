#!/usr/bin/env bash
set -euo pipefail
mkdir -p reportes-locales
opa test politica -v | tee reportes-locales/opa-pruebas.txt
opa eval --fail --data politica/compose.rego --input infra/compose.yaml   'data.laboratorio.permit' | tee reportes-locales/opa-permitida.json
docker compose -f infra/compose.yaml config -q
docker compose -f infra/compose.yaml build
trivy image --format json --output reportes-locales/trivy.json   --severity HIGH,CRITICAL --exit-code 1 solicitudes-internas:lab
