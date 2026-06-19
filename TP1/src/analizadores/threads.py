# analizadores/threads.py - Analizador que extrae info de los threads (LWPs) de cada proceso

import os
import time
from procfs import leer_stat


def correr_threads(pids_compartidos, snapshot, intervalo, evento_apagado):
    while not evento_apagado.is_set():
        datos_threads = {}

        for pid in list(pids_compartidos):
            try:
                tids = os.listdir(f'/proc/{pid}/task')
                threads = []

                for tid in tids:
                    try:
                        stat = leer_stat(int(tid))
                        with open(f'/proc/{pid}/task/{tid}/comm', 'r') as f:
                            nombre = f.read().strip()
                        threads.append({
                            'tid': int(tid),
                            'nombre': nombre,
                            'estado': stat['estado']
                        })
                    except (FileNotFoundError, ProcessLookupError):
                        continue

                datos_threads[pid] = threads

            except (FileNotFoundError, ProcessLookupError):
                continue

        snapshot['threads'] = datos_threads
        snapshot['threads_ts'] = time.time()

        time.sleep(intervalo)