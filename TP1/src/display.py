# display.py - Proceso que renderiza la interfaz de texto (TUI) usando curses

import curses
import time


VISTAS = {
    1: 'Resumen',
    2: 'Memoria',
    3: 'File Descriptors',
    4: 'Threads',
    5: 'Senales',
    6: 'Scheduling',
    7: 'Sistema'
}

TECLAS_VISTA = {
    ord('1'): 1, ord('r'): 1,
    ord('2'): 2, ord('m'): 2,
    ord('3'): 3, ord('f'): 3,
    ord('4'): 4, ord('t'): 4,
    ord('5'): 5, ord('s'): 5,
    ord('6'): 6, ord('p'): 6,
    ord('7'): 7, ord('g'): 7,
}


def correr_display(snapshot_compartido, intervalo, evento_apagado):
    curses.wrapper(loop_display, snapshot_compartido, intervalo, evento_apagado)


def loop_display(stdscr, snapshot_compartido, intervalo, evento_apagado):
    curses.curs_set(0)
    stdscr.nodelay(True)

    vista_activa = 1

    while not evento_apagado.is_set():
        stdscr.clear()
        altura, ancho = stdscr.getmaxyx()

        titulo = f"MONITOR DE PROCESOS | Vista: {VISTAS[vista_activa]} | teclas 1-7 | q=salir"
        stdscr.addstr(0, 0, titulo[:ancho-1])
        stdscr.addstr(1, 0, "-" * (ancho - 1))

        fila = 2

        if vista_activa == 1:
            fila = dibujar_resumen(stdscr, snapshot_compartido, fila, altura, ancho)
        elif vista_activa == 2:
            fila = dibujar_memoria(stdscr, snapshot_compartido, fila, altura, ancho)
        elif vista_activa == 3:
            fila = dibujar_fds(stdscr, snapshot_compartido, fila, altura, ancho)
        elif vista_activa == 4:
            fila = dibujar_threads(stdscr, snapshot_compartido, fila, altura, ancho)
        elif vista_activa == 5:
            fila = dibujar_senales(stdscr, snapshot_compartido, fila, altura, ancho)
        elif vista_activa == 6:
            fila = dibujar_scheduling(stdscr, snapshot_compartido, fila, altura, ancho)
        elif vista_activa == 7:
            stdscr.addstr(fila, 0, "Vista Sistema - proximamente")

        stdscr.refresh()

        tecla = stdscr.getch()
        if tecla == ord('q'):
            evento_apagado.set()
        elif tecla in TECLAS_VISTA:
            vista_activa = TECLAS_VISTA[tecla]

        time.sleep(intervalo)


def dibujar_resumen(stdscr, snapshot, fila, altura, ancho):
    stdscr.addstr(fila, 0, "PID".ljust(8) + "PPID".ljust(8) + "NOMBRE".ljust(20) + "ESTADO".ljust(8) + "THREADS")
    fila += 1
    datos = snapshot.get('resumen', {})
    for pid, d in datos.items():
        if fila >= altura - 1:
            break
        linea = (str(pid).ljust(8) + str(d['ppid']).ljust(8) +
                 d['nombre'].ljust(20) + d['estado'].ljust(8) +
                 str(d['threads']))
        stdscr.addstr(fila, 0, linea[:ancho-1])
        fila += 1
    return fila


def dibujar_memoria(stdscr, snapshot, fila, altura, ancho):
    stdscr.addstr(fila, 0, "PID".ljust(8) + "VmRSS".ljust(15) + "VmSize".ljust(15) + "VmSwap")
    fila += 1
    datos = snapshot.get('memoria', {})
    for pid, d in datos.items():
        if fila >= altura - 1:
            break
        linea = (str(pid).ljust(8) + str(d['vmrss']).ljust(15) +
                 str(d['vmsize']).ljust(15) + str(d['vmswap']))
        stdscr.addstr(fila, 0, linea[:ancho-1])
        fila += 1
    return fila


def dibujar_fds(stdscr, snapshot, fila, altura, ancho):
    stdscr.addstr(fila, 0, "PID".ljust(8) + "FD".ljust(6) + "TIPO".ljust(10) + "DESTINO")
    fila += 1
    datos = snapshot.get('fds', {})
    for pid, fds in datos.items():
        for fd in fds:
            if fila >= altura - 1:
                break
            linea = (str(pid).ljust(8) + str(fd['fd']).ljust(6) +
                     fd['tipo'].ljust(10) + fd['destino'])
            stdscr.addstr(fila, 0, linea[:ancho-1])
            fila += 1
    return fila


def dibujar_threads(stdscr, snapshot, fila, altura, ancho):
    stdscr.addstr(fila, 0, "PID".ljust(8) + "TID".ljust(8) + "NOMBRE".ljust(20) + "ESTADO")
    fila += 1
    datos = snapshot.get('threads', {})
    for pid, threads in datos.items():
        for t in threads:
            if fila >= altura - 1:
                break
            linea = (str(pid).ljust(8) + str(t['tid']).ljust(8) +
                     t['nombre'].ljust(20) + t['estado'])
            stdscr.addstr(fila, 0, linea[:ancho-1])
            fila += 1
    return fila


def dibujar_senales(stdscr, snapshot, fila, altura, ancho):
    stdscr.addstr(fila, 0, "PID".ljust(8) + "CATEGORIA".ljust(14) + "SENALES")
    fila += 1
    datos = snapshot.get('senales', {})
    for pid, d in datos.items():
        for categoria, senales in d.items():
            if fila >= altura - 1:
                break
            if senales:
                linea = (str(pid).ljust(8) + categoria.ljust(14) +
                         ', '.join(senales))
                stdscr.addstr(fila, 0, linea[:ancho-1])
                fila += 1
    return fila


def dibujar_scheduling(stdscr, snapshot, fila, altura, ancho):
    stdscr.addstr(fila, 0, "PID".ljust(8) + "NOMBRE".ljust(20) + "PRIO".ljust(6) +
                  "NICE".ljust(6) + "POLITICA".ljust(10) + "VOL_CTX".ljust(10) + "INVOL_CTX")
    fila += 1
    datos = snapshot.get('scheduling', {})
    for pid, d in datos.items():
        if fila >= altura - 1:
            break
        linea = (str(pid).ljust(8) + d['nombre'].ljust(20) +
                 str(d['prioridad']).ljust(6) + str(d['nice']).ljust(6) +
                 d['politica'].ljust(10) + str(d['voluntary_ctx']).ljust(10) +
                 str(d['involuntary_ctx']))
        stdscr.addstr(fila, 0, linea[:ancho-1])
        fila += 1
    return fila