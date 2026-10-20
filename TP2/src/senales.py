import asyncio
import json
import time
import signal
import logging

logger = logging.getLogger(__name__)


def configurar_señales(app_state: dict) -> None:
    loop = asyncio.get_event_loop()

    def manejar_shutdown(sig):
        logger.info(f"Señal {sig.name} recibida, iniciando shutdown ordenado...")
        asyncio.create_task(shutdown_ordenado(app_state))

    loop.add_signal_handler(signal.SIGTERM, lambda: manejar_shutdown(signal.SIGTERM))
    loop.add_signal_handler(signal.SIGINT, lambda: manejar_shutdown(signal.SIGINT))


async def shutdown_ordenado(app_state: dict) -> None:
    from src.cola import almacen
    from src.modelos import EstadoTarea

    logger.info("Dejando de aceptar tareas nuevas...")
    app_state["aceptando_tareas"] = False

    # Esperar hasta 10 segundos a que terminen las tareas en curso
    limite = 10
    inicio = time.time()
    while time.time() - inicio < limite:
        ejecutando = [
            t for t in almacen.tareas.values()
            if t.estado == EstadoTarea.EJECUTANDO
        ]
        if not ejecutando:
            break
        logger.info(f"Esperando {len(ejecutando)} tareas en curso...")
        await asyncio.sleep(1)

    # Volcar estado a JSON
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"estado_{timestamp}.json"
    datos = {id: tarea.a_dict() for id, tarea in almacen.tareas.items()}

    with open(nombre_archivo, "w") as f:
        json.dump(datos, f, indent=2, default=str)

    logger.info(f"Estado volcado a {nombre_archivo}")

    # Cancelar workers
    for task in app_state.get("workers", []):
        task.cancel()

    loop = asyncio.get_event_loop()
    loop.stop()
