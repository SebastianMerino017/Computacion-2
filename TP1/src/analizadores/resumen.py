# analizadores/resumen.py - Analizador que extrae info basica de cada proceso

import time
from procfs import leer_stat, leer_status


def leer_jiffies(pid):
    # Lee utime y stime del campo 14 y 15 de /proc/<pid>/stat
    with open(f'/proc/{pid}/stat', 'r') as f:
        contenido = f.read()
    fin_nombre = contenido.rindex(')')
    campos = contenido[fin_nombre + 2:].split()
    utime = int(campos[11])
    stime = int(campos[12])
    return utime + stime


def correr_resumen(pids_compartidos, snapshot, intervalo, evento_apagado):
    jiffies_anterior = {}

    while not evento_apagado.is_set():
        datos_resumen = {}
        jiffies_actual = {}

        for pid in list(pids_compartidos):
            try:
                stat = leer_stat(pid)
                status = leer_status(pid)
                jiffies = leer_jiffies(pid)
                jiffies_actual[pid] = jiffies

                if pid in jiffies_anterior:
                    delta = jiffies_actual[pid] - jiffies_anterior[pid]
                    cpu_pct = round(delta / intervalo, 1)
                else:
                    cpu_pct = 0.0

                datos_resumen[pid] = {
                    'pid': pid,
                    'ppid': status.get('PPid', '?'),
                    'estado': stat['estado'],
                    'nombre': stat['nombre'],
                    'threads': status.get('Threads', '?'),
                    'cpu_pct': cpu_pct
                }
            except (FileNotFoundError, ProcessLookupError):
                continue

        jiffies_anterior = jiffies_actual
        snapshot['resumen'] = datos_resumen
        snapshot['resumen_ts'] = time.time()

        time.sleep(intervalo)