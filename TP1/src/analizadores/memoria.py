# analizadores/memoria.py

import time
from procfs import leer_status


def correr_memoria(pids_compartidos, snapshot, intervalo_value, evento_apagado):
    while not evento_apagado.is_set():
        datos_memoria = {}

        for pid in list(pids_compartidos):
            try:
                status = leer_status(pid)
                datos_memoria[pid] = {
                    'vmsize': status.get('VmSize', '?'),
                    'vmrss': status.get('VmRSS', '?'),
                    'vmdata': status.get('VmData', '?'),
                    'vmstk': status.get('VmStk', '?'),
                    'vmexe': status.get('VmExe', '?'),
                    'vmlib': status.get('VmLib', '?'),
                    'vmhwm': status.get('VmHWM', '?'),
                    'vmswap': status.get('VmSwap', '?')
                }
            except (FileNotFoundError, ProcessLookupError):
                continue

        snapshot['memoria'] = datos_memoria
        snapshot['memoria_ts'] = time.time()

        time.sleep(intervalo_value.value)