# recolector.py - Proceso que mantiene actualizada la lista de PIDs activos

import time
from procfs import listar_pids


def correr_recolector(pids_compartidos, intervalo_value, evento_apagado):
    while not evento_apagado.is_set():
        pids_compartidos[:] = listar_pids()
        time.sleep(intervalo_value.value)