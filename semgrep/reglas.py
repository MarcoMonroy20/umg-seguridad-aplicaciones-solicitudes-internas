from os import environ
from secrets import token_urlsafe

# ruleid: credencial-de-entorno-con-valor-fijo
value = environ.get("SOLICITANTE_TOKEN", "ejemplo-estatico")

# ok: credencial-de-entorno-con-valor-fijo
value = environ.get("SOLICITANTE_TOKEN") or token_urlsafe(32)
