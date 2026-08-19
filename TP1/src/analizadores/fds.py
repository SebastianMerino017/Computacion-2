# analizadores/fds.py

import os
import time


def correr_fds(pids_compartidos, snapshot, intervalo_value, evento_apagado):
    while not evento_apagado.is_set():
        datos_fds = {}

        for pid in list(pids_compartidos):
            try:
                fds = []
                fd_dir = f'/proc/{pid}/fd'

                for fd in os.listdir(fd_dir):
                    try:
                        destino = os.readlink(f'{fd_dir}/{fd}')
                        tipo = inferir_tipo(destino)
                        fds.append({
                            'fd': int(fd),
                            'destino': destino,
                            'tipo': tipo
                        })
                    except (FileNotFoundError, PermissionError):
                        continue

                datos_fds[pid] = fds

            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue

        snapshot['fds'] = datos_fds
        snapshot['fds_ts'] = time.time()

        time.sleep(intervalo_value.value)


def inferir_tipo(destino):
    if destino.startswith('socket:'):
        return 'socket'
    elif destino.startswith('pipe:'):
        return 'pipe'
    elif destino.startswith('/dev/pts'):
        return 'tty'
    elif destino.startswith('/'):
        return 'file'
    else:
        return 'otro'