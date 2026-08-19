# senales.py - Handlers de señales del monitor

import signal
import os
import json
import time


# Flags compartidos entre el handler y el loop principal
_flag_dump = False
_flag_reload = False
_flag_verbose = False


def configurar_handlers(evento_apagado, snapshot, valores_intervalos):

    def manejar_apagado(numero_senal, frame):
        evento_apagado.set()

    def manejar_dump(numero_senal, frame):
        # Solo prende el flag, el trabajo real lo hace el loop principal
        global _flag_dump
        _flag_dump = True

    def manejar_reload(numero_senal, frame):
        global _flag_reload
        _flag_reload = True

    def manejar_verbose(numero_senal, frame):
        global _flag_verbose
        _flag_verbose = not _flag_verbose

    signal.signal(signal.SIGINT, manejar_apagado)
    signal.signal(signal.SIGTERM, manejar_apagado)
    signal.signal(signal.SIGUSR1, manejar_dump)
    signal.signal(signal.SIGHUP, manejar_reload)
    signal.signal(signal.SIGUSR2, manejar_verbose)


def procesar_flags(snapshot, valores_intervalos):
    # Llamado desde el loop principal — hace el trabajo real de los flags
    global _flag_dump, _flag_reload, _flag_verbose

    if _flag_dump:
        _flag_dump = False
        try:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f'src/dump_{timestamp}.json'
            datos = dict(snapshot)
            import json
            with open(nombre_archivo, 'w') as f:
                json.dump(datos, f, indent=2, default=str)
        except Exception:
            pass

    if _flag_reload:
        _flag_reload = False
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            intervalos = config['intervalos']
            for clave, value in valores_intervalos.items():
                if clave in intervalos:
                    value.value = float(intervalos[clave])
        except Exception:
            pass

    return _flag_verbose


def es_verbose():
    return _flag_verbose