# analizadores/sistema.py

import time
import os


def leer_cpu():
    with open('/proc/stat', 'r') as f:
        linea = f.readline()
    campos = linea.split()
    user = int(campos[1])
    nice = int(campos[2])
    system = int(campos[3])
    idle = int(campos[4])
    iowait = int(campos[5])
    total = user + nice + system + idle + iowait
    return {'user': user, 'nice': nice, 'system': system,
            'idle': idle, 'iowait': iowait, 'total': total}


def leer_meminfo():
    datos = {}
    with open('/proc/meminfo', 'r') as f:
        for linea in f:
            clave, _, valor = linea.partition(':')
            datos[clave.strip()] = valor.strip()
    return datos


def leer_loadavg():
    with open('/proc/loadavg', 'r') as f:
        contenido = f.read().split()
    return {'avg1': contenido[0], 'avg5': contenido[1],
            'avg15': contenido[2], 'procesos': contenido[3]}


def leer_uptime():
    with open('/proc/uptime', 'r') as f:
        contenido = f.read().split()
    segundos = float(contenido[0])
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    return f'{horas}h {minutos}m {segs}s'


def correr_sistema(pids_compartidos, snapshot, intervalo_value, evento_apagado):
    cpu_anterior = None

    while not evento_apagado.is_set():
        try:
            cpu_actual = leer_cpu()
            if cpu_anterior is not None:
                delta_total = cpu_actual['total'] - cpu_anterior['total']
                delta_idle = cpu_actual['idle'] - cpu_anterior['idle']
                cpu_uso = round(100 * (1 - delta_idle / delta_total), 1) if delta_total > 0 else 0.0
            else:
                cpu_uso = 0.0
            cpu_anterior = cpu_actual

            meminfo = leer_meminfo()
            loadavg = leer_loadavg()
            uptime = leer_uptime()

            snapshot['sistema'] = {
                'cpu_uso': cpu_uso,
                'mem_total': meminfo.get('MemTotal', '?'),
                'mem_libre': meminfo.get('MemFree', '?'),
                'mem_disponible': meminfo.get('MemAvailable', '?'),
                'buffers': meminfo.get('Buffers', '?'),
                'cached': meminfo.get('Cached', '?'),
                'swap_total': meminfo.get('SwapTotal', '?'),
                'swap_libre': meminfo.get('SwapFree', '?'),
                'load_avg1': loadavg['avg1'],
                'load_avg5': loadavg['avg5'],
                'load_avg15': loadavg['avg15'],
                'procesos': loadavg['procesos'],
                'uptime': uptime,
            }
            snapshot['sistema_ts'] = time.time()

        except Exception:
            pass

        time.sleep(intervalo_value.value)