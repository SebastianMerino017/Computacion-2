import asyncio
import time
import logging
from src.modelos import EstadoTarea, TipoTarea
from src.cola import almacen
from src.tareas import ejecutar_descargar, ejecutar_hashear, ejecutar_esperar
from src.eventos import gestor_eventos

logger = logging.getLogger(__name__)


async def notificar_cambio(tarea_id: str, estado: str, detalle: str = None) -> None:
    mensaje = {"tarea_id": tarea_id, "estado": estado}
    if detalle:
        mensaje["detalle"] = detalle
    await gestor_eventos.notificar(mensaje)


async def procesar_tarea(tarea_id: str, loop: asyncio.AbstractEventLoop) -> None:
    tarea = almacen.obtener(tarea_id)
    if not tarea:
        return

    tarea.estado = EstadoTarea.EJECUTANDO
    tarea.iniciada_en = time.time()
    await notificar_cambio(tarea_id, "ejecutando")

    try:
        async with asyncio.timeout(tarea.timeout):
            if tarea.tipo == TipoTarea.DESCARGAR:
                resultado = await ejecutar_descargar(tarea.parametros)
            elif tarea.tipo == TipoTarea.HASHEAR:
                resultado = await ejecutar_hashear(tarea.parametros, loop)
            elif tarea.tipo == TipoTarea.ESPERAR:
                resultado = await ejecutar_esperar(tarea.parametros)
            else:
                raise ValueError(f"Tipo de tarea desconocido: {tarea.tipo}")

        tarea.resultado = resultado
        tarea.estado = EstadoTarea.COMPLETADA
        await notificar_cambio(tarea_id, "completada")

    except asyncio.CancelledError:
        tarea.estado = EstadoTarea.CANCELADA
        tarea.error = "Cancelada por el usuario"
        await notificar_cambio(tarea_id, "cancelada", "Cancelada por el usuario")

    except TimeoutError:
        tarea.estado = EstadoTarea.FALLIDA
        tarea.error = f"Timeout después de {tarea.timeout} segundos"
        await notificar_cambio(tarea_id, "fallida", tarea.error)
        await intentar_reintento(tarea, loop)

    except Exception as e:
        tarea.estado = EstadoTarea.FALLIDA
        tarea.error = str(e)
        await notificar_cambio(tarea_id, "fallida", str(e))
        await intentar_reintento(tarea, loop)

    finally:
        tarea.finalizada_en = time.time()
        almacen.tasks_asyncio.pop(tarea_id, None)


async def intentar_reintento(tarea, loop: asyncio.AbstractEventLoop) -> None:
    if tarea.reintentos_realizados < tarea.max_reintentos:
        tarea.reintentos_realizados += 1
        espera = 2 ** (tarea.reintentos_realizados - 1)
        logger.info(f"Reintentando tarea {tarea.id} en {espera}s (intento {tarea.reintentos_realizados}/{tarea.max_reintentos})")
        await notificar_cambio(tarea.id, "reintentando", f"Intento {tarea.reintentos_realizados}/{tarea.max_reintentos} en {espera}s")
        await asyncio.sleep(espera)
        tarea.estado = EstadoTarea.PENDIENTE
        tarea.error = None
        tarea.finalizada_en = None
        await almacen.cola.put(tarea.id)


async def worker(worker_id: int, loop: asyncio.AbstractEventLoop) -> None:
    while True:
        tarea_id = await almacen.cola.get()

        tarea = almacen.obtener(tarea_id)
        if tarea and tarea.estado == EstadoTarea.CANCELADA:
            almacen.cola.task_done()
            continue

        task = asyncio.create_task(procesar_tarea(tarea_id, loop))
        almacen.tasks_asyncio[tarea_id] = task

        try:
            await task
        except Exception:
            pass
        finally:
            almacen.cola.task_done()


async def iniciar_workers(cantidad: int = 5) -> list:
    loop = asyncio.get_event_loop()
    workers = [
        asyncio.create_task(worker(i, loop))
        for i in range(cantidad)
    ]
    return workers