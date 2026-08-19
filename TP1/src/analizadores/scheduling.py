# analizadores/scheduling.py

import time
from procfs import leer_stat, leer_status


POLITICAS = {
    0: 'NORMAL',
    1: 'FIFO',
    2: 'RR',
    3: 'BATCH',
    5: 'IDLE',
    6: 'DEADLINE'
}


def correr_scheduling(pids_compartidos, snapshot, intervalo_value, evento_apagado):
    while not evento_apagado.is_set():
        datos_scheduling = {}

        for pid in list(pids_compartidos):
            try:
                stat = leer_stat(pid)
                status = leer_status(pid)
                campos = leer_stat_completo(pid)

                datos_scheduling[pid] = {
                    'nombre': stat['nombre'],
                    'prioridad': campos[17],
                    'nice': campos[18],
                    'politica': POLITICAS.get(int(campos[40]), f'UNKNOWN({campos[40]})'),
                    'rt_prioridad': campos[39],
                    'cpus_allowed': status.get('Cpus_allowed_list', '?'),
                    'voluntary_ctx': status.get('voluntary_ctxt_switches', '?'),
                    'involuntary_ctx': status.get('nonvoluntary_ctxt_switches', '?'),
                    'utime': campos[13],
                    'stime': campos[14],
                }
            except (FileNotFoundError, ProcessLookupError, IndexError):
                continue

        snapshot['scheduling'] = datos_scheduling
        snapshot['scheduling_ts'] = time.time()

        time.sleep(intervalo_value.value)


def leer_stat_completo(pid):
    with open(f'/proc/{pid}/stat', 'r') as f:
        contenido = f.read()
    fin_nombre = contenido.rindex(')')
    resto = contenido[fin_nombre + 2:].split()
    return resto