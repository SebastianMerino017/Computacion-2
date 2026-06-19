# analizadores/resumen.py - Analizador que extrae info basica de cada proceso

import time
from procfs import leer_stat, leer_status


def correr_resumen(pids_compartidos, snapshot, intervalo, evento_apagado):
    while not evento_apagado.is_set():
        datos_resumen = {}

        for pid in list(pids_compartidos):
            try:
                stat = leer_stat(pid)
                status = leer_status(pid)
                datos_resumen[pid] = {
                    'pid': pid,
                    'ppid': status.get('PPid', '?'),
                    'estado': stat['estado'],
                    'nombre': stat['nombre'],
                    'threads': status.get('Threads', '?')
                }
            except (FileNotFoundError, ProcessLookupError):
                continue

        snapshot['resumen'] = datos_resumen
        snapshot['resumen_ts'] = time.time()

        time.sleep(intervalo)