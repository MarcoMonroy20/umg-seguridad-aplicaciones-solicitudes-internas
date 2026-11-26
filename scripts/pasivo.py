"""Observación pasiva de dos rutas públicas fijas en el laboratorio local."""
import json
from urllib.request import urlopen

base = "http://127.0.0.1:8000"
results = []
for path in ("/", "/openapi.json"):
    with urlopen(base + path, timeout=5) as response:
        headers = {
            name: response.headers.get(name)
            for name in ("Content-Type", "Cache-Control", "X-Content-Type-Options", "Content-Security-Policy",
                         "Cross-Origin-Resource-Policy")
        }
        body = json.load(response)
        results.append({"ruta": path, "estado": response.status, "cabeceras": headers,
                        "rutas_declaradas": sorted(body.get("paths", {}))})
print(json.dumps(results, ensure_ascii=True, indent=2))
