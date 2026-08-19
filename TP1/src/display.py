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

VISTA_A_CLAVE = {
    1: 'resumen', 2: 'memoria', 3: 'fds',
    4: 'threads', 5: 'senales', 6: 'scheduling', 7: 'sistema'
}

COLOR_NORMAL = 1
COLOR_RUNNING = 2
COLOR_ZOMBIE = 3
COLOR_HEADER = 4
COLOR_SEPARADOR = 5


def iniciar_colores():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_NORMAL, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_RUNNING, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_ZOMBIE, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_HEADER, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_SEPARADOR, curses.COLOR_YELLOW, -1)


def color_por_estado(estado):
    if estado == 'R':
        return curses.color_pair(COLOR_RUNNING)
    elif estado == 'Z':
        return curses.color_pair(COLOR_ZOMBIE)
    else:
        return curses.color_pair(COLOR_NORMAL)


def correr_display(snapshot_compartido, intervalo, evento_apagado, valores_intervalos, intervalos_minimos):
    curses.wrapper(loop_display, snapshot_compartido, intervalo, evento_apagado, valores_intervalos, intervalos_minimos)


def loop_display(stdscr, snapshot_compartido, intervalo, evento_apagado, valores_intervalos, intervalos_minimos):
    curses.curs_set(0)
    stdscr.timeout(100)
    iniciar_colores()

    vista_activa = 1

    while not evento_apagado.is_set():
        stdscr.clear()
        altura, ancho = stdscr.getmaxyx()

        titulo = f"MONITOR DE PROCESOS | Vista: {VISTAS[vista_activa]} | teclas 1-7 | +/- intervalo | q=salir"
        stdscr.addstr(0, 0, titulo[:ancho-1], curses.color_pair(COLOR_HEADER))
        stdscr.addstr(1, 0, "-" * (ancho - 1), curses.color_pair(COLOR_SEPARADOR))

        clave = VISTA_A_CLAVE.get(vista_activa)
        if clave and clave in valores_intervalos:
            intervalo_actual = valores_intervalos[clave].value
            stdscr.addstr(2, 0, f"Intervalo: {intervalo_actual:.1f}s", curses.color_pair(COLOR_NORMAL))

        fila = 3

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
            fila = dibujar_sistema(stdscr, snapshot_compartido, fila, altura, ancho)

        stdscr.refresh()

        tecla = stdscr.getch()
        if tecla == ord('q'):
            evento_apagado.set()
        elif tecla in TECLAS_VISTA:
            vista_activa = TECLAS_VISTA[tecla]
        elif tecla == ord('+') and clave in valores_intervalos:
            valores_intervalos[clave].value = round(
                valores_intervalos[clave].value + 0.5, 1)
        elif tecla == ord('-') and clave in valores_intervalos:
            minimo = intervalos_minimos.get(clave, 0.5)
            nuevo = round(valores_intervalos[clave].value - 0.5, 1)
            if nuevo >= minimo:
                valores_intervalos[clave].value = nuevo


def dibujar_resumen(stdscr, snapshot, fila, altura, ancho):
    stdscr.addstr(fila, 0,
        "PID".ljust(8) + "PPID".ljust(8) + "NOMBRE".ljust(20) +
        "ESTADO".ljust(8) + "THREADS".ljust(10) + "CPU%",
        curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
    fila += 1
    datos = snapshot.get('resumen', {})
    for pid, d in datos.items():
        if fila >= altura - 1:
            break
        estado = d['estado']
        color = color_por_estado(estado)
        linea = (str(pid).ljust(8) + str(d['ppid']).ljust(8) +
                 d['nombre'].ljust(20) + estado.ljust(8) +
                 str(d['threads']).ljust(10) + str(d['cpu_pct']))
        stdscr.addstr(fila, 0, linea[:ancho-1], color)
        fila += 1
    return fila


def dibujar_memoria(stdscr, snapshot, fila, altura, ancho):
    stdscr.addstr(fila, 0,
        "PID".ljust(8) + "VmRSS".ljust(15) + "VmSize".ljust(15) + "VmSwap",
        curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
    fila += 1
    datos = snapshot.get('memoria', {})
    for pid, d in datos.items():
        if fila >= altura - 1:
            break
        linea = (str(pid).ljust(8) + str(d['vmrss']).ljust(15) +
                 str(d['vmsize']).ljust(15) + str(d['vmswap']))
        stdscr.addstr(fila, 0, linea[:ancho-1], curses.color_pair(COLOR_NORMAL))
        fila += 1
    return fila


def dibujar_fds(stdscr, snapshot, fila, altura, ancho):
    stdscr.addstr(fila, 0,
        "PID".ljust(8) + "FD".ljust(6) + "TIPO".ljust(10) + "DESTINO",
        curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
    fila += 1
    datos = snapshot.get('fds', {})
    for pid, fds in datos.items():
        for fd in fds:
            if fila >= altura - 1:
                break
            linea = (str(pid).ljust(8) + str(fd['fd']).ljust(6) +
                     fd['tipo'].ljust(10) + fd['destino'])
            stdscr.addstr(fila, 0, linea[:ancho-1], curses.color_pair(COLOR_NORMAL))
            fila += 1
    return fila


def dibujar_threads(stdscr, snapshot, fila, altura, ancho):
    stdscr.addstr(fila, 0,
        "PID".ljust(8) + "TID".ljust(8) + "NOMBRE".ljust(20) + "ESTADO",
        curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
    fila += 1
    datos = snapshot.get('threads', {})
    for pid, threads in datos.items():
        for t in threads:
            if fila >= altura - 1:
                break
            color = color_por_estado(t['estado'])
            linea = (str(pid).ljust(8) + str(t['tid']).ljust(8) +
                     t['nombre'].ljust(20) + t['estado'])
            stdscr.addstr(fila, 0, linea[:ancho-1], color)
            fila += 1
    return fila


def dibujar_senales(stdscr, snapshot, fila, altura, ancho):
    stdscr.addstr(fila, 0,
        "PID".ljust(8) + "CATEGORIA".ljust(14) + "SENALES",
        curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
    fila += 1
    datos = snapshot.get('senales', {})
    for pid, d in datos.items():
        for categoria, senales in d.items():
            if fila >= altura - 1:
                break
            if senales:
                linea = (str(pid).ljust(8) + categoria.ljust(14) +
                         ', '.join(senales))
                stdscr.addstr(fila, 0, linea[:ancho-1], curses.color_pair(COLOR_NORMAL))
                fila += 1
    return fila


def dibujar_scheduling(stdscr, snapshot, fila, altura, ancho):
    stdscr.addstr(fila, 0,
        "PID".ljust(8) + "NOMBRE".ljust(20) + "PRIO".ljust(6) +
        "NICE".ljust(6) + "POLITICA".ljust(10) + "VOL_CTX".ljust(10) + "INVOL_CTX",
        curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
    fila += 1
    datos = snapshot.get('scheduling', {})
    for pid, d in datos.items():
        if fila >= altura - 1:
            break
        linea = (str(pid).ljust(8) + d['nombre'].ljust(20) +
                 str(d['prioridad']).ljust(6) + str(d['nice']).ljust(6) +
                 d['politica'].ljust(10) + str(d['voluntary_ctx']).ljust(10) +
                 str(d['involuntary_ctx']))
        stdscr.addstr(fila, 0, linea[:ancho-1], curses.color_pair(COLOR_NORMAL))
        fila += 1
    return fila


def dibujar_sistema(stdscr, snapshot, fila, altura, ancho):
    datos = snapshot.get('sistema', {})
    if not datos:
        stdscr.addstr(fila, 0, "Cargando datos del sistema...",
                      curses.color_pair(COLOR_NORMAL))
        return fila

    stdscr.addstr(fila, 0, f"Uptime: {datos['uptime']}", curses.color_pair(COLOR_NORMAL))
    fila += 1
    stdscr.addstr(fila, 0, f"CPU uso: {datos['cpu_uso']}%", curses.color_pair(COLOR_RUNNING))
    fila += 1
    stdscr.addstr(fila, 0,
        f"Load average: {datos['load_avg1']} {datos['load_avg5']} {datos['load_avg15']}",
        curses.color_pair(COLOR_NORMAL))
    fila += 1
    stdscr.addstr(fila, 0, f"Procesos activos: {datos['procesos']}",
                  curses.color_pair(COLOR_NORMAL))
    fila += 2

    stdscr.addstr(fila, 0, "--- MEMORIA ---", curses.color_pair(COLOR_SEPARADOR))
    fila += 1
    stdscr.addstr(fila, 0, f"Total:      {datos['mem_total']}", curses.color_pair(COLOR_NORMAL))
    fila += 1
    stdscr.addstr(fila, 0, f"Libre:      {datos['mem_libre']}", curses.color_pair(COLOR_NORMAL))
    fila += 1
    stdscr.addstr(fila, 0, f"Disponible: {datos['mem_disponible']}", curses.color_pair(COLOR_NORMAL))
    fila += 1
    stdscr.addstr(fila, 0, f"Buffers:    {datos['buffers']}", curses.color_pair(COLOR_NORMAL))
    fila += 1
    stdscr.addstr(fila, 0, f"Cached:     {datos['cached']}", curses.color_pair(COLOR_NORMAL))
    fila += 1
    stdscr.addstr(fila, 0, f"Swap total: {datos['swap_total']}", curses.color_pair(COLOR_NORMAL))
    fila += 1
    stdscr.addstr(fila, 0, f"Swap libre: {datos['swap_libre']}", curses.color_pair(COLOR_NORMAL))
    fila += 1

    return fila