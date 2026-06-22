# main.py - Punto de entrada del monitor. Arranca los procesos y coordina todo

import multiprocessing
import time
import traceback
import json
from recolector import correr_recolector
from analizadores.resumen import correr_resumen
from analizadores.memoria import correr_memoria
from analizadores.threads import correr_threads
from analizadores.fds import correr_fds
from analizadores.senales import correr_senales
from analizadores.scheduling import correr_scheduling
from analizadores.sistema import correr_sistema
from display import correr_display
from senales import configurar_handlers


def log_error(mensaje):
    with open('src/debug.log', 'a') as f:
        f.write(mensaje + '\n')


def cargar_config():
    with open('config.json', 'r') as f:
        return json.load(f)


def main():
    try:
        config = cargar_config()
        intervalos = config['intervalos']
        intervalo_display = config['display']['intervalo']

        evento_apagado = multiprocessing.Event()

        manager = multiprocessing.Manager()
        pids = manager.list()
        snapshot = manager.dict()

        configurar_handlers(evento_apagado, snapshot)

        procesos = []

        procesos.append(multiprocessing.Process(
            target=correr_recolector,
            args=(pids, intervalos['recolector'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_resumen,
            args=(pids, snapshot, intervalos['resumen'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_memoria,
            args=(pids, snapshot, intervalos['memoria'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_threads,
            args=(pids, snapshot, intervalos['threads'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_fds,
            args=(pids, snapshot, intervalos['fds'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_senales,
            args=(pids, snapshot, intervalos['senales'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_scheduling,
            args=(pids, snapshot, intervalos['scheduling'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_sistema,
            args=(pids, snapshot, intervalos['sistema'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_display,
            args=(snapshot, intervalo_display, evento_apagado)
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