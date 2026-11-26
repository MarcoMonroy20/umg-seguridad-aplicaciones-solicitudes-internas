#!/usr/bin/env bash
set -euo pipefail
mkdir -p reportes-locales
# Se ejecuta en Linux y debe encontrarse iniciada la API en loopback.
docker run --rm --network host   --mount "type=bind,source=$(pwd)/reportes-locales,target=/zap/wrk"   ghcr.io/zaproxy/zaproxy:stable   zap-baseline.py -t http://127.0.0.1:8000/ -m 1 -J zap.json -r zap.html
