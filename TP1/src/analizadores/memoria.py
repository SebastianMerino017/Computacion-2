# analizadores/memoria.py - Analizador que extrae info de memoria de cada proceso

import time
from procfs import leer_status


def leer_maps(pid):
    # Lee /proc/<pid>/maps y agrupa las regiones en segmentos
    segmentos = {
        'text': 0,
        'data': 0,
        'heap': 0,
        'stack': 0,
        'shared': 0,
        'otro': 0
    }

    try:
        with open(f'/proc/{pid}/maps', 'r') as f:
            for linea in f:
                partes = linea.split()
                if len(partes) < 5:
                    continue

                rango = partes[0]
                permisos = partes[1]
                nombre = partes[-1] if len(partes) >= 6 else ''

                # Calcular tamaño de la region en KB
                inicio, fin = rango.split('-')
                tamanio = (int(fin, 16) - int(inicio, 16)) // 1024

                if '[heap]' in nombre:
                    segmentos['heap'] += tamanio
                elif '[stack]' in nombre:
                    segmentos['stack'] += tamanio
                elif 'x' in permisos and permisos[1] != 'w':
                    # Ejecutable sin escritura = codigo (text)
                    segmentos['text'] += tamanio
                elif permisos[1] == 'w' and 's' not in permisos:
                    # Escribible y privado = datos
                    segmentos['data'] += tamanio
                elif 's' in permisos:
                    # Compartido
                    segmentos['shared'] += tamanio
                else:
                    segmentos['otro'] += tamanio

    except (FileNotFoundError, PermissionError):
        pass

    return segmentos


def correr_memoria(pids_compartidos, snapshot, intervalo_value, evento_apagado):
    while not evento_apagado.is_set():
        datos_memoria = {}

        for pid in list(pids_compartidos):
            try:
                status = leer_status(pid)
                maps = leer_maps(pid)
                datos_memoria[pid] = {
                    'vmsize': status.get('VmSize', '?'),
                    'vmrss': status.get('VmRSS', '?'),
                    'vmdata': status.get('VmData', '?'),
                    'vmstk': status.get('VmStk', '?'),
                    'vmexe': status.get('VmExe', '?'),
                    'vmlib': status.get('VmLib', '?'),
                    'vmhwm': status.get('VmHWM', '?'),
                    'vmswap': status.get('VmSwap', '?'),
                    'maps': maps
                }
            except (FileNotFoundError, ProcessLookupError):
                continue

        snapshot['memoria'] = datos_memoria
        snapshot['memoria_ts'] = time.time()

        time.sleep(intervalo_value.value)