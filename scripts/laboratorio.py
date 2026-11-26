"""Inicia Uvicorn y registra únicamente observación HTTP de lectura local."""
import subprocess
import sys
from pathlib import Path
from time import monotonic, sleep
from urllib.error import URLError
from urllib.request import urlopen

reports = Path("reportes-locales")
reports.mkdir(exist_ok=True)
with (reports / "uvicorn.log").open("w", encoding="utf-8") as log:
    server = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "api:from_environment", "--factory",
        "--host", "127.0.0.1", "--port", "8000", "--no-server-header",
    ], stdout=log, stderr=log)
    try:
        deadline = monotonic() + 15
        while monotonic() < deadline:
            if server.poll() is not None:
                raise RuntimeError("Uvicorn terminó antes de responder. Consulte uvicorn.log.")
            try:
                with urlopen("http://127.0.0.1:8000/", timeout=1):
                    break
            except URLError:
                sleep(0.2)
        else:
            raise RuntimeError("Uvicorn no respondió dentro del plazo.")
        with (reports / "http-pasivo.json").open("w", encoding="utf-8") as output:
            subprocess.run([sys.executable, "scripts/pasivo.py"], stdout=output, check=True)
    finally:
        server.terminate()
        server.wait(timeout=10)
