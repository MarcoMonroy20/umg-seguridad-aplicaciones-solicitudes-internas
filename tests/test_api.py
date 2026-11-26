import logging
from secrets import token_urlsafe
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api import create_app


@pytest.fixture
def lab():
    first, second = token_urlsafe(32), token_urlsafe(32)
    with TestClient(create_app(first, second)) as client:
        yield client, {"Authorization": f"Bearer {first}"}, {"Authorization": f"Bearer {second}"}


def submit(client, headers):
    response = client.post("/solicitudes", json={"title": "Acceso interno"}, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_propietario(lab, caplog):
    client, first, _ = lab
    item = submit(client, first)
    path = f"/solicitudes/{item['id']}"
    with caplog.at_level(logging.INFO, logger="solicitudes.autorizacion"):
        response = client.get(path, headers=first)
    assert response.status_code == 200
    assert response.json() == item
    assert item["owner"] == "cuenta-a"
    assert "lectura=permitida cuenta=cuenta-a" in caplog.messages
    assert first["Authorization"] not in caplog.text


def test_aislamiento_de_propietario(lab):
    client, first, second = lab
    item = submit(client, first)
    denied = client.get(f"/solicitudes/{item['id']}", headers=second)
    missing = client.get(f"/solicitudes/{uuid4()}", headers=second)
    assert denied.status_code == missing.status_code == 404
    assert denied.json() == missing.json()


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer credencial-invalida"}])
def test_autenticacion(lab, headers):
    client, _, _ = lab
    response = client.get(f"/solicitudes/{uuid4()}", headers=headers)
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize("payload", [
    {"title": "válido", "owner": "cuenta-b"}, {"title": "   "},
    {"title": 42}, {"title": "x" * 121}, {"title": "válido", "status": "aprobada"},
])
def test_contrato_estricto(lab, payload):
    client, first, _ = lab
    assert client.post("/solicitudes", json=payload, headers=first).status_code == 422


def test_transicion_y_rol(lab):
    client, first, second = lab
    item = submit(client, first)
    path = f"/solicitudes/{item['id']}"
    approval = path + "/aprobacion"
    assert client.post(approval, headers=first).status_code == 403
    assert client.get(path, headers=first).json()["status"] == "pendiente"
    assert client.post(approval, headers=second).json()["status"] == "aprobada"
    assert client.post(approval, headers=second).status_code == 409
    assert client.get(path, headers=first).json()["status"] == "aprobada"


def test_autoaprobacion(lab):
    client, _, supervisor = lab
    item = submit(client, supervisor)
    path = f"/solicitudes/{item['id']}"
    assert client.post(path + "/aprobacion", headers=supervisor).status_code == 403
    assert client.get(path, headers=supervisor).json()["status"] == "pendiente"


def test_cabeceras_publicas(lab):
    client, _, _ = lab
    for path in ("/", "/openapi.json"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
        assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_uuid_invalido(lab):
    client, first, _ = lab
    assert client.get("/solicitudes/invalido", headers=first).status_code == 422
