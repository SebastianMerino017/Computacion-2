# main.py - Punto de entrada del monitor. Arranca los procesos y coordina todo

import multiprocessing
import time
import traceback
from recolector import correr_recolector
from analizadores.resumen import correr_resumen
from analizadores.memoria import correr_memoria
from analizadores.threads import correr_threads
from analizadores.fds import correr_fds
from analizadores.senales import correr_senales
from analizadores.scheduling import correr_scheduling
from display import correr_display
from senales import configurar_handlers


def log_error(mensaje):
    with open('src/debug.log', 'a') as f:
        f.write(mensaje + '\n')


def main():
    try:
        evento_apagado = multiprocessing.Event()
        configurar_handlers(evento_apagado)

        manager = multiprocessing.Manager()
        pids = manager.list()
        snapshot = manager.dict()

        procesos = []

        procesos.append(multiprocessing.Process(
            target=correr_recolector,
            args=(pids, 1, evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_resumen,
            args=(pids, snapshot, 2, evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_memoria,
            args=(pids, snapshot, 3, evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_threads,
            args=(pids, snapshot, 2, evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_fds,
            args=(pids, snapshot, 5, evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_senales,
            args=(pids, snapshot, 10, evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_scheduling,
            args=(pids, snapshot, 10, evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_display,
            args=(snapshot, 0.5, evento_apagado)
        ))

        for p in procesos:
            p.start()

        while not evento_apagado.is_set():
            time.sleep(0.2)

        for p in procesos:
            p.terminate()
        for p in procesos:
            p.join(timeout=3)

        manager.shutdown()

    except Exception:
        log_error('EXCEPCION:\n' + traceback.format_exc())


if __name__ == '__main__':
    main()