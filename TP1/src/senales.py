# senales.py - Handlers de señales del monitor

import signal
import os


def configurar_handlers(evento_apagado):

    def manejar_apagado(numero_senal, frame):
        with open('src/debug.log', 'a') as f:
            f.write(f'Senal {numero_senal} recibida en PID {os.getpid()}\n')
        evento_apagado.set()

    signal.signal(signal.SIGINT, manejar_apagado)
    signal.signal(signal.SIGTERM, manejar_apagado)