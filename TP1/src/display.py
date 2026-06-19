# display.py - Proceso que renderiza la interfaz de texto (TUI) usando curses

import curses
import time


def correr_display(snapshot_compartido, intervalo, evento_apagado):
    curses.wrapper(loop_display, snapshot_compartido, intervalo, evento_apagado)


def loop_display(stdscr, snapshot_compartido, intervalo, evento_apagado):
    curses.curs_set(0)
    stdscr.nodelay(True)

    while not evento_apagado.is_set():
        stdscr.clear()

        stdscr.addstr(0, 0, "MONITOR DE PROCESOS - q para salir")
        stdscr.addstr(1, 0, "PID".ljust(8) + "PPID".ljust(8) + "NOMBRE".ljust(20) + "ESTADO".ljust(8) + "THREADS")

        altura, ancho = stdscr.getmaxyx()
        fila = 2

        datos_resumen = snapshot_compartido.get('resumen', {})

        for pid, datos in datos_resumen.items():
            if fila >= altura - 1:
                break
            linea = (str(pid).ljust(8) + str(datos['ppid']).ljust(8) +
                     datos['nombre'].ljust(20) + datos['estado'].ljust(8) +
                     str(datos['threads']))
            stdscr.addstr(fila, 0, linea)
            fila += 1

        fila += 1
        if fila < altura - 1:
            stdscr.addstr(fila, 0, "--- MEMORIA ---")
            fila += 1

        if fila < altura - 1:
            stdscr.addstr(fila, 0, "PID".ljust(8) + "VmRSS".ljust(15) + "VmSize".ljust(15) + "VmSwap")
            fila += 1

        datos_memoria = snapshot_compartido.get('memoria', {})

        for pid, datos in datos_memoria.items():
            if fila >= altura - 1:
                break
            linea = (str(pid).ljust(8) + str(datos['vmrss']).ljust(15) +
                     str(datos['vmsize']).ljust(15) + str(datos['vmswap']))
            stdscr.addstr(fila, 0, linea)
            fila += 1

        fila += 1
        if fila < altura - 1:
            stdscr.addstr(fila, 0, "--- THREADS ---")
            fila += 1

        if fila < altura - 1:
            stdscr.addstr(fila, 0, "PID".ljust(8) + "TID".ljust(8) + "NOMBRE".ljust(20) + "ESTADO")
            fila += 1

        datos_threads = snapshot_compartido.get('threads', {})

        for pid, threads in datos_threads.items():
            for t in threads:
                if fila >= altura - 1:
                    break
                linea = (str(pid).ljust(8) + str(t['tid']).ljust(8) +
                         t['nombre'].ljust(20) + t['estado'])
                stdscr.addstr(fila, 0, linea)
                fila += 1

        stdscr.refresh()

        tecla = stdscr.getch()
        if tecla == ord('q'):
            evento_apagado.set()

        time.sleep(intervalo)