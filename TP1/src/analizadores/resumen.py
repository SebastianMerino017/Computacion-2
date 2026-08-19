# resumen.py - Analizador de resumen de procesos
import time
from procfs import leer_stat, leer_status


def leer_jiffies(pid):
    with open(f'/proc/{pid}/stat', 'r') as f:
        contenido = f.read()
    fin_nombre = contenido.rindex(')')
    campos = contenido[fin_nombre + 2:].split()
    utime = int(campos[11])
    stime = int(campos[12])
    return utime + stime


def correr_resumen(pids_compartidos, snapshot, intervalo_value, evento_apagado):
    jiffies_anterior = {}
    tiempo_anterior = time.time()

    while not evento_apagado.is_set():
        datos_resumen = {}
        jiffies_actual = {}
        tiempo_actual = time.time()
        delta_tiempo = tiempo_actual - tiempo_anterior
        hz = 100
        try:
            import os
            hz = os.sysconf('SC_CLK_TCK')
        except Exception:
            pass

        for pid in list(pids_compartidos):
            try:
                stat = leer_stat(pid)
                status = leer_status(pid)
                jiffies = leer_jiffies(pid)
                jiffies_actual[pid] = jiffies

                if pid in jiffies_anterior and delta_tiempo > 0:
                    delta_j = jiffies_actual[pid] - jiffies_anterior[pid]
                    cpu_pct = round((delta_j / hz) / delta_tiempo * 100, 1)
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
        tiempo_anterior = tiempo_actual
        snapshot['resumen'] = datos_resumen
        snapshot['resumen_ts'] = time.time()

        time.sleep(intervalo_value.value)