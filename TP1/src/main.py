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
from senales import configurar_handlers, procesar_flags


INTERVALOS_MINIMOS = {
    'resumen': 0.5,
    'memoria': 1.0,
    'fds': 2.0,
    'threads': 0.5,
    'senales': 5.0,
    'scheduling': 5.0,
    'sistema': 1.0,
    'recolector': 0.5,
}


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

        valores_intervalos = {
            'recolector': multiprocessing.Value('d', intervalos['recolector']),
            'resumen':    multiprocessing.Value('d', intervalos['resumen']),
            'memoria':    multiprocessing.Value('d', intervalos['memoria']),
            'threads':    multiprocessing.Value('d', intervalos['threads']),
            'fds':        multiprocessing.Value('d', intervalos['fds']),
            'senales':    multiprocessing.Value('d', intervalos['senales']),
            'scheduling': multiprocessing.Value('d', intervalos['scheduling']),
            'sistema':    multiprocessing.Value('d', intervalos['sistema']),
        }

        configurar_handlers(evento_apagado, snapshot, valores_intervalos)

        procesos = []

        procesos.append(multiprocessing.Process(
            target=correr_recolector,
            args=(pids, valores_intervalos['recolector'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_resumen,
            args=(pids, snapshot, valores_intervalos['resumen'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_memoria,
            args=(pids, snapshot, valores_intervalos['memoria'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_threads,
            args=(pids, snapshot, valores_intervalos['threads'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_fds,
            args=(pids, snapshot, valores_intervalos['fds'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_senales,
            args=(pids, snapshot, valores_intervalos['senales'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_scheduling,
            args=(pids, snapshot, valores_intervalos['scheduling'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_sistema,
            args=(pids, snapshot, valores_intervalos['sistema'], evento_apagado)
        ))

        procesos.append(multiprocessing.Process(
            target=correr_display,
            args=(snapshot, intervalo_display, evento_apagado,
                  valores_intervalos, INTERVALOS_MINIMOS)
        ))

        for p in procesos:
            p.start()

        while not evento_apagado.is_set():
            procesar_flags(snapshot, valores_intervalos)
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