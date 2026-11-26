import logging
from dataclasses import dataclass
from secrets import token_urlsafe
from threading import Lock
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, StringConstraints

logger = logging.getLogger("solicitudes.autorizacion")
bearer = HTTPBearer(auto_error=False)
Text = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=3, max_length=120)]


@dataclass(frozen=True)
class Account:
    name: str
    role: Literal["solicitante", "supervisor"]


class NewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Text


class InternalRequest(NewRequest):
    id: UUID
    owner: str
    status: Literal["pendiente", "aprobada"]


def create_app(requester_token: str, supervisor_token: str) -> FastAPI:
    if min(len(requester_token), len(supervisor_token)) < 32 or requester_token == supervisor_token:
        raise ValueError("Se requieren dos credenciales distintas de al menos 32 caracteres.")

    accounts = {
        requester_token: Account("cuenta-a", "solicitante"),
        supervisor_token: Account("cuenta-b", "supervisor"),
    }
    records: dict[UUID, InternalRequest] = {}
    lock = Lock()
    app = FastAPI(title="Solicitudes internas", docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        return response

    def authenticate(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> Account:
        account = accounts.get(credentials.credentials) if credentials else None
        if account is None:
            logger.info("autenticacion=denegada")
            raise HTTPException(401, "Credencial requerida o inválida", headers={"WWW-Authenticate": "Bearer"})
        return account

    # La forma de valor predeterminado evita referencias locales diferidas.
    @app.get("/")
    def health():
        return JSONResponse({"estado": "disponible", "contrato": "/openapi.json"})

    @app.post("/solicitudes", status_code=201)
    def submit(payload: NewRequest, account: Account = Depends(authenticate)) -> InternalRequest:
        item = InternalRequest(id=uuid4(), owner=account.name, title=payload.title, status="pendiente")
        with lock:
            records[item.id] = item
        return item

    @app.get("/solicitudes/{request_id}")
    def read(request_id: UUID, account: Account = Depends(authenticate)) -> InternalRequest:
        with lock:
            item = records.get(request_id)
        if item is None or item.owner != account.name:
            logger.info("lectura=denegada cuenta=%s", account.name)
            raise HTTPException(404, "Solicitud inexistente")
        logger.info("lectura=permitida cuenta=%s", account.name)
        return item

    @app.post("/solicitudes/{request_id}/aprobacion")
    def approve(request_id: UUID, account: Account = Depends(authenticate)) -> InternalRequest:
        if account.role != "supervisor":
            logger.info("aprobacion=denegada cuenta=%s", account.name)
            raise HTTPException(403, "Operación reservada a supervisión")
        with lock:
            item = records.get(request_id)
            if item is None:
                raise HTTPException(404, "Solicitud inexistente")
            if item.owner == account.name:
                raise HTTPException(403, "No se permite la autoaprobación")
            if item.status != "pendiente":
                raise HTTPException(409, "Transición de estado inválida")
            updated = item.model_copy(update={"status": "aprobada"})
            records[request_id] = updated
        logger.info("aprobacion=permitida cuenta=%s", account.name)
        return updated


    return app


def from_environment() -> FastAPI:
    from os import environ

    return create_app(
        environ.get("SOLICITANTE_TOKEN") or token_urlsafe(32),
        environ.get("SUPERVISOR_TOKEN") or token_urlsafe(32),
    )
