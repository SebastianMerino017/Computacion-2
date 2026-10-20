import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.cola import almacen
from src.modelos import EstadoTarea


@pytest.fixture(autouse=True)
def limpiar_almacen():
    # Limpia el almacen antes de cada test
    almacen.tareas.clear()
    almacen.tasks_asyncio.clear()
    while not almacen.cola.empty():
        try:
            almacen.cola.get_nowait()
        except Exception:
            break


@pytest.fixture
def cliente():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ─── Tests básicos de endpoints ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_crear_tarea_esperar(cliente):
    async with cliente as c:
        resp = await c.post("/tareas", json={
            "tipo": "esperar",
            "parametros": {"segundos": 1}
        })
    assert resp.status_code == 202
    data = resp.json()
    assert "id" in data
    assert data["estado"] == "pendiente"


@pytest.mark.asyncio
async def test_obtener_tarea_existente(cliente):
    async with cliente as c:
        resp = await c.post("/tareas", json={
            "tipo": "esperar",
            "parametros": {"segundos": 1}
        })
        tarea_id = resp.json()["id"]

        resp2 = await c.get(f"/tareas/{tarea_id}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == tarea_id


@pytest.mark.asyncio
async def test_obtener_tarea_inexistente(cliente):
    async with cliente as c:
        resp = await c.get("/tareas/id-que-no-existe")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_listar_tareas(cliente):
    async with cliente as c:
        await c.post("/tareas", json={"tipo": "esperar", "parametros": {"segundos": 1}})
        await c.post("/tareas", json={"tipo": "esperar", "parametros": {"segundos": 1}})
        resp = await c.get("/tareas")
    assert resp.status_code == 200
    assert len(resp.json()["tareas"]) == 2


@pytest.mark.asyncio
async def test_listar_tareas_filtro_estado(cliente):
    async with cliente as c:
        await c.post("/tareas", json={"tipo": "esperar", "parametros": {"segundos": 1}})
        resp = await c.get("/tareas?estado=pendiente")
    assert resp.status_code == 200
    tareas = resp.json()["tareas"]
    assert all(t["estado"] == "pendiente" for t in tareas)


@pytest.mark.asyncio
async def test_cancelar_tarea_pendiente(cliente):
    async with cliente as c:
        resp = await c.post("/tareas", json={
            "tipo": "esperar",
            "parametros": {"segundos": 60}
        })
        tarea_id = resp.json()["id"]

        resp2 = await c.delete(f"/tareas/{tarea_id}")
        assert resp2.status_code == 200

        resp3 = await c.get(f"/tareas/{tarea_id}")
        assert resp3.json()["estado"] == "cancelada"


@pytest.mark.asyncio
async def test_cancelar_tarea_inexistente(cliente):
    async with cliente as c:
        resp = await c.delete("/tareas/id-que-no-existe")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_estadisticas(cliente):
    async with cliente as c:
        await c.post("/tareas", json={"tipo": "esperar", "parametros": {"segundos": 1}})
        resp = await c.get("/estadisticas")
    assert resp.status_code == 200
    data = resp.json()
    assert "totales_por_estado" in data
    assert "tiempo_promedio" in data
    assert "workers_ocupados" in data


@pytest.mark.asyncio
async def test_tipo_tarea_invalido(cliente):
    async with cliente as c:
        resp = await c.post("/tareas", json={
            "tipo": "tipo_invalido",
            "parametros": {}
        })
    assert resp.status_code == 422


# ─── Tests de hashear ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_hashear_devuelve_hash(cliente):
    async with cliente as c:
        resp = await c.post("/tareas", json={
            "tipo": "hashear",
            "parametros": {"texto": "test", "iteraciones": 100}
        })
    assert resp.status_code == 202
    assert resp.json()["estado"] == "pendiente"
