# analizadores/senales.py - Analizador que extrae info de señales de cada proceso

import time
from procfs import leer_status


# Mapa de número de señal a nombre
NOMBRES_SENALES = {
    1: 'SIGHUP', 2: 'SIGINT', 3: 'SIGQUIT', 4: 'SIGILL',
    5: 'SIGTRAP', 6: 'SIGABRT', 7: 'SIGBUS', 8: 'SIGFPE',
    9: 'SIGKILL', 10: 'SIGUSR1', 11: 'SIGSEGV', 12: 'SIGUSR2',
    13: 'SIGPIPE', 14: 'SIGALRM', 15: 'SIGTERM', 17: 'SIGCHLD',
    18: 'SIGCONT', 19: 'SIGSTOP', 20: 'SIGTSTP', 21: 'SIGTTIN',
    22: 'SIGTTOU', 23: 'SIGURG', 24: 'SIGXCPU', 25: 'SIGXFSZ',
    26: 'SIGVTALRM', 27: 'SIGPROF', 28: 'SIGWINCH', 29: 'SIGIO',
    30: 'SIGPWR', 31: 'SIGSYS'
}


def decodificar_mascara(hex_str):
    # Convierte una mascara hexadecimal a lista de nombres de señales activas
    try:
        mascara = int(hex_str, 16)
    except (ValueError, TypeError):
        return []

    senales_activas = []
    for bit in range(64):
        if mascara & (1 << bit):
            numero = bit + 1
            nombre = NOMBRES_SENALES.get(numero, f'SIG{numero}')
            senales_activas.append(nombre)
    return senales_activas


def correr_senales(pids_compartidos, snapshot, intervalo, evento_apagado):
    while not evento_apagado.is_set():
        datos_senales = {}

        for pid in list(pids_compartidos):
            try:
                status = leer_status(pid)
                datos_senales[pid] = {
                    'bloqueadas': decodificar_mascara(status.get('SigBlk', '0')),
                    'ignoradas':  decodificar_mascara(status.get('SigIgn', '0')),
                    'capturadas': decodificar_mascara(status.get('SigCgt', '0')),
                    'pendientes': decodificar_mascara(status.get('SigPnd', '0')),
                }
            except (FileNotFoundError, ProcessLookupError):
                continue

        snapshot['senales'] = datos_senales
        snapshot['senales_ts'] = time.time()

        time.sleep(intervalo)