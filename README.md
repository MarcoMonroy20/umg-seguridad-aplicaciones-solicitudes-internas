# Solicitudes internas

API de laboratorio para Seguridad en Aplicaciones, Universidad Mariano Gálvez de Guatemala. Trabaja con datos ficticios, dos identidades y almacenamiento en memoria. Ejecutar únicamente en el equipo local. La decisión técnica sobre producción es de rechazo.

## Inicio rápido

Requiere Python 3.12. Cree y active un entorno virtual con `python -m venv .venv`. En PowerShell use `& .\.venv\Scripts\Activate.ps1` y en bash use `source .venv/bin/activate`.

```text
python -m pip install --require-hashes -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pytest -q --junitxml=reportes-locales/pytest.xml
python scripts/laboratorio.py
```

El último comando arranca Uvicorn en 127.0.0.1:8000, consulta dos rutas públicas y detiene el proceso. Use un puerto 8000 libre. Los reportes nuevos se escriben en `reportes-locales/`. Las salidas de la evaluación original están en `evidencias/`.

Para una sesión interactiva en PowerShell, genere las dos credenciales en la misma consola y ejecute:

```powershell
$env:SOLICITANTE_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:SUPERVISOR_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
python -m uvicorn api:from_environment --factory --host 127.0.0.1 --port 8000 --no-server-header
```

| Ruta | Condición de acceso | Resultado |
|---|---|---|
| GET / y GET /openapi.json | Pública | Estado y contrato |
| POST /solicitudes | Cualquier cuenta autenticada | Crea una solicitud pendiente a nombre de esa cuenta |
| GET /solicitudes/{UUID} | Propietario | Devuelve su solicitud |
| POST /solicitudes/{UUID}/aprobacion | Supervisor y solicitud de otra cuenta, pendiente | Cambia el estado a aprobada |

El alta recibe JSON con `title`, texto estricto de 3 a 120 caracteres tras eliminar espacios extremos. Use el encabezado `Authorization: Bearer <credencial>` en rutas protegidas. Cada proceso mantiene su propio estado. Los tokens de laboratorio carecen de vencimiento dentro del proceso y requieren rotación por reinicio.

## Controles reproducibles

```text
semgrep --test semgrep/
semgrep scan --metrics=off --config semgrep/reglas.yaml --error --json --output reportes-locales/semgrep.json api.py
pip-audit --disable-pip --no-deps --require-hashes -r requirements.txt --format json -o reportes-locales/pip-audit.json
cyclonedx-py requirements requirements.txt --output-reproducible --sv 1.6 -o reportes-locales/sbom.cdx.json
opa test politica -v
opa eval --fail -d politica/compose.rego -i infra/compose.yaml data.laboratorio.permit
opa eval --fail -d politica/compose.rego -i infra/denegada.yaml data.laboratorio.permit
```

Use OPA 1.0.0 o compatible con Rego v1. La última evaluación debe devolver 1. `infra/denegada.yaml` es exclusivamente una entrada estática. Para Docker Compose y Trivy, desde la raíz ejecute `bash scripts/infra.sh`. Para ZAP Baseline, en un host Linux con Docker, inicie la API en 127.0.0.1:8000 y ejecute `bash scripts/zap-baseline.sh` con el directorio de reportes escribible por el contenedor. La ejecución de ZAP debe mantenerse en modo Baseline. Consulte la evidencia y sus límites antes de interpretar alertas o desplegar.

Para repetir la evaluación pasiva ejecutada, inicie la API en loopback y ejecute ZAP 2.17.0 con Java 17 o superior desde la raíz del proyecto. Sustituya RUTA por la ubicación de su distribución.

```text
java -jar RUTA/zap-2.17.0.jar -cmd -silent -autorun scripts/zap-pasivo.yaml
```

El plan solo envía dos solicitudes GET y guarda el reporte en `reportes-locales/zap-pasivo.json`. La evaluación ZAP mediante Automation Framework es distinta del empaquetado Baseline.

## Integración continua

GitHub Actions está configurado para verificar pruebas, Semgrep, avisos de dependencias, SBOM y OPA antes de construir una imagen y observar el servicio local. Un fallo de pytest, una coincidencia ERROR de SAST, cualquier aviso de SCA o una denegación de OPA bloquean el trabajo. Las advertencias requieren revisión. El archivo de flujo no equivale a una ejecución remota.

Las verificaciones de política asociadas a las dos revisiones locales se registran en `evidencias/revisiones-opa.txt`. `historial.bundle` permite inspeccionarlas sin alojamiento remoto. Desde la carpeta extraída, use `git clone historial.bundle historial` y `git -C historial log --oneline`. El árbol del ZIP incluye los reportes incorporados después de estas revisiones.

