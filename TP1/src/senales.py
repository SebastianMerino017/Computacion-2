# senales.py - Handlers de señales del monitor

import signal
import os
import json
import time


def configurar_handlers(evento_apagado, snapshot):

    def manejar_apagado(numero_senal, frame):
        evento_apagado.set()

    def manejar_dump(numero_senal, frame):
        try:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f'src/dump_{timestamp}.json'
            datos = dict(snapshot)
            with open(nombre_archivo, 'w') as f:
                json.dump(datos, f, indent=2, default=str)
        except Exception as e:
            pass

    signal.signal(signal.SIGINT, manejar_apagado)
    signal.signal(signal.SIGTERM, manejar_apagado)
    signal.signal(signal.SIGUSR1, manejar_dump)