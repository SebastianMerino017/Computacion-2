import asyncio
import time
from src.modelos import EstadoTarea, TipoTarea
from src.cola import almacen
from src.tareas import ejecutar_descargar, ejecutar_hashear, ejecutar_esperar


async def procesar_tarea(tarea_id: str, loop: asyncio.AbstractEventLoop) -> None:
    tarea = almacen.obtener(tarea_id)
    if not tarea:
        return

    tarea.estado = EstadoTarea.EJECUTANDO
    tarea.iniciada_en = time.time()

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

    except asyncio.CancelledError:
        tarea.estado = EstadoTarea.CANCELADA
        tarea.error = "Cancelada por el usuario"

    except TimeoutError:
        tarea.estado = EstadoTarea.FALLIDA
        tarea.error = f"Timeout después de {tarea.timeout} segundos"

    except Exception as e:
        tarea.estado = EstadoTarea.FALLIDA
        tarea.error = str(e)

    finally:
        tarea.finalizada_en = time.time()
        almacen.tasks_asyncio.pop(tarea_id, None)


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
