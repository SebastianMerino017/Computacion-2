import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.cola import almacen
from src.modelos import EstadoTarea, TipoTarea, Tarea
from src.workers import iniciar_workers
from src.senales import configurar_señales
from src.eventos import gestor_eventos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app_state = {
    "aceptando_tareas": True,
    "workers": []
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando workers...")
    app_state["workers"] = await iniciar_workers(cantidad=5)
    configurar_señales(app_state)

    import glob
    volcados = glob.glob("estado_*.json")
    if volcados:
        logger.info(f"Volcado previo encontrado: {sorted(volcados)[-1]}")

    yield

    logger.info("Apagando workers...")
    for w in app_state["workers"]:
        w.cancel()


app = FastAPI(title="Plataforma de Tareas Distribuidas", lifespan=lifespan)


class CrearTareaRequest(BaseModel):
    tipo: TipoTarea
    parametros: dict
    timeout: float = 30.0
    max_reintentos: int = 0


@app.post("/tareas", status_code=202)
async def crear_tarea(request: CrearTareaRequest):
    if not app_state["aceptando_tareas"]:
        raise HTTPException(status_code=503, detail="El servidor no acepta tareas nuevas")

    tarea = Tarea(
        tipo=request.tipo,
        parametros=request.parametros,
        timeout=request.timeout,
        max_reintentos=request.max_reintentos
    )
    almacen.agregar(tarea)
    await almacen.cola.put(tarea.id)

    return {"id": tarea.id, "estado": tarea.estado}


@app.get("/tareas")
async def listar_tareas(estado: Optional[EstadoTarea] = None):
    tareas = almacen.listar(estado)
    return {"tareas": [t.a_dict() for t in tareas]}


@app.get("/tareas/{id}")
async def obtener_tarea(id: str):
    tarea = almacen.obtener(id)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return tarea.a_dict()


@app.delete("/tareas/{id}")
async def cancelar_tarea(id: str):
    tarea = almacen.obtener(id)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    if tarea.estado in (EstadoTarea.COMPLETADA, EstadoTarea.FALLIDA, EstadoTarea.CANCELADA):
        raise HTTPException(status_code=400, detail=f"No se puede cancelar una tarea en estado {tarea.estado}")

    task = almacen.tasks_asyncio.get(id)
    if task:
        task.cancel()
    else:
        import time
        tarea.estado = EstadoTarea.CANCELADA
        tarea.error = "Cancelada antes de ejecutarse"
        tarea.finalizada_en = time.time()

    return {"id": id, "estado": "cancelada"}


@app.get("/estadisticas")
async def estadisticas():
    return almacen.estadisticas()


@app.websocket("/eventos")
async def websocket_eventos(websocket: WebSocket):
    await gestor_eventos.conectar(websocket)
    try:
        await websocket.send_json({"tipo": "conectado", "mensaje": "Escuchando eventos de tareas"})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        gestor_eventos.desconectar(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)