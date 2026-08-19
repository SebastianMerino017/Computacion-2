# analizadores/threads.py - CORREGIDO: usa /proc/<pid>/task/<tid>/stat

import os
import time


def leer_stat_thread(pid, tid):
    # Ruta correcta para threads secundarios
    with open(f'/proc/{pid}/task/{tid}/stat', 'r') as f:
        contenido = f.read()
    fin_nombre = contenido.rindex(')')
    campos = contenido[fin_nombre + 2:].split()
    estado = campos[0]
    return estado


def correr_threads(pids_compartidos, snapshot, intervalo_value, evento_apagado):
    while not evento_apagado.is_set():
        datos_threads = {}

        for pid in list(pids_compartidos):
            try:
                tids = os.listdir(f'/proc/{pid}/task')
                threads = []

                for tid in tids:
                    try:
                        estado = leer_stat_thread(pid, tid)
                        with open(f'/proc/{pid}/task/{tid}/comm', 'r') as f:
                            nombre = f.read().strip()
                        threads.append({
                            'tid': int(tid),
                            'nombre': nombre,
                            'estado': estado
                        })
                    except (FileNotFoundError, ProcessLookupError):
                        continue

                datos_threads[pid] = threads

            except (FileNotFoundError, ProcessLookupError):
                continue

        snapshot['threads'] = datos_threads
        snapshot['threads_ts'] = time.time()

        time.sleep(intervalo_value.value)