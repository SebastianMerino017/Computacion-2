# display.py - Proceso que renderiza la interfaz de texto (TUI) usando curses

import curses


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
COLOR_SELECCION = 6


def iniciar_colores():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_NORMAL, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_RUNNING, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_ZOMBIE, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_HEADER, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_SEPARADOR, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_SELECCION, curses.COLOR_BLACK, curses.COLOR_CYAN)


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
    indice_seleccion = 0
    scroll_offset = 0
    mostrar_ayuda = False

    while not evento_apagado.is_set():
        stdscr.clear()
        altura, ancho = stdscr.getmaxyx()

        # Encabezado
        titulo = f"MONITOR DE PROCESOS | Vista: {VISTAS[vista_activa]} | 1-7 +/- flechas Enter h=ayuda q=salir"
        stdscr.addstr(0, 0, titulo[:ancho-1], curses.color_pair(COLOR_HEADER))
        stdscr.addstr(1, 0, "-" * (ancho - 1), curses.color_pair(COLOR_SEPARADOR))

        clave = VISTA_A_CLAVE.get(vista_activa)
        if clave and clave in valores_intervalos:
            intervalo_actual = valores_intervalos[clave].value
            stdscr.addstr(2, 0, f"Intervalo: {intervalo_actual:.1f}s", curses.color_pair(COLOR_NORMAL))

        # Obtener lista de procesos del snapshot
        datos_resumen = snapshot_compartido.get('resumen', {})
        pids_lista = sorted(datos_resumen.keys())

        if mostrar_ayuda:
            dibujar_ayuda(stdscr, 3, altura, ancho)
        elif vista_activa == 7:
            # Vista sistema no tiene lista/detalle, ocupa toda la pantalla
            dibujar_sistema(stdscr, snapshot_compartido, 3, altura, ancho)
        else:
            # Calcular alturas de paneles
            altura_lista = (altura - 3) // 2
            fila_separador = 3 + altura_lista
            altura_detalle = altura - fila_separador - 1

            # Ajustar seleccion
            if pids_lista:
                indice_seleccion = max(0, min(indice_seleccion, len(pids_lista) - 1))
                if indice_seleccion >= scroll_offset + altura_lista - 1:
                    scroll_offset = indice_seleccion - altura_lista + 2
                if indice_seleccion < scroll_offset:
                    scroll_offset = indice_seleccion
                scroll_offset = max(0, scroll_offset)

            # Panel superior — lista de procesos
            dibujar_lista_procesos(stdscr, datos_resumen, pids_lista,
                                   indice_seleccion, scroll_offset,
                                   3, altura_lista, ancho)

            # Separador entre paneles
            if fila_separador < altura - 1:
                pid_sel = pids_lista[indice_seleccion] if pids_lista else None
                sep = f"--- Detalle PID {pid_sel} | Vista: {VISTAS[vista_activa]} ---"
                stdscr.addstr(fila_separador, 0,
                              sep[:ancho-1],
                              curses.color_pair(COLOR_SEPARADOR))

            # Panel inferior — detalle del proceso seleccionado
            if pids_lista and fila_separador + 1 < altura - 1:
                pid_sel = pids_lista[indice_seleccion]
                dibujar_detalle(stdscr, snapshot_compartido, vista_activa,
                                pid_sel, fila_separador + 1,
                                fila_separador + 1 + altura_detalle, ancho)

        stdscr.refresh()

        tecla = stdscr.getch()
        if tecla == ord('q'):
            evento_apagado.set()
        elif tecla == ord('h') or tecla == ord('?'):
            mostrar_ayuda = not mostrar_ayuda
        elif tecla in TECLAS_VISTA:
            vista_activa = TECLAS_VISTA[tecla]
            mostrar_ayuda = False
        elif tecla == curses.KEY_UP:
            indice_seleccion = max(0, indice_seleccion - 1)
        elif tecla == curses.KEY_DOWN:
            if pids_lista:
                indice_seleccion = min(len(pids_lista) - 1, indice_seleccion + 1)
        elif tecla == ord('+') and clave in valores_intervalos:
            valores_intervalos[clave].value = round(
                valores_intervalos[clave].value + 0.5, 1)
        elif tecla == ord('-') and clave in valores_intervalos:
            minimo = intervalos_minimos.get(clave, 0.5)
            nuevo = round(valores_intervalos[clave].value - 0.5, 1)
            if nuevo >= minimo:
                valores_intervalos[clave].value = nuevo


def dibujar_lista_procesos(stdscr, datos_resumen, pids_lista, indice_sel, scroll_offset, fila_inicio, altura_panel, ancho):
    # Header de la lista
    stdscr.addstr(fila_inicio, 0,
        "PID".ljust(8) + "NOMBRE".ljust(20) + "ESTADO".ljust(8) + "THREADS".ljust(10) + "CPU%",
        curses.color_pair(COLOR_HEADER) | curses.A_BOLD)

    fila = fila_inicio + 1
    fin = fila_inicio + altura_panel

    for i in range(scroll_offset, len(pids_lista)):
        if fila >= fin:
            break
        pid = pids_lista[i]
        d = datos_resumen.get(pid, {})
        estado = d.get('estado', '?')

        linea = (str(pid).ljust(8) + d.get('nombre', '?').ljust(20) +
                 estado.ljust(8) + str(d.get('threads', '?')).ljust(10) +
                 str(d.get('cpu_pct', '?')))

        if i == indice_sel:
            stdscr.addstr(fila, 0, linea[:ancho-1], curses.color_pair(COLOR_SELECCION))
        else:
            stdscr.addstr(fila, 0, linea[:ancho-1], color_por_estado(estado))
        fila += 1


def dibujar_detalle(stdscr, snapshot, vista_activa, pid, fila_inicio, fila_fin, ancho):
    fila = fila_inicio

    if vista_activa == 1:
        datos = snapshot.get('resumen', {}).get(pid, {})
        if datos:
            stdscr.addstr(fila, 0, f"PID:     {datos.get('pid', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"PPID:    {datos.get('ppid', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"Nombre:  {datos.get('nombre', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"Estado:  {datos.get('estado', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"Threads: {datos.get('threads', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"CPU%:    {datos.get('cpu_pct', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1

    elif vista_activa == 2:
        datos = snapshot.get('memoria', {}).get(pid, {})
        if datos:
            maps = datos.get('maps', {})
            stdscr.addstr(fila, 0, f"VmRSS:   {datos.get('vmrss', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"VmSize:  {datos.get('vmsize', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"VmHWM:   {datos.get('vmhwm', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"VmSwap:  {datos.get('vmswap', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"Text:    {maps.get('text', 0)} kB", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"Data:    {maps.get('data', 0)} kB", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"Heap:    {maps.get('heap', 0)} kB", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"Stack:   {maps.get('stack', 0)} kB", curses.color_pair(COLOR_NORMAL)); fila += 1

    elif vista_activa == 3:
        fds = snapshot.get('fds', {}).get(pid, [])
        stdscr.addstr(fila, 0, f"FDs abiertos: {len(fds)}", curses.color_pair(COLOR_NORMAL)); fila += 1
        for fd in fds:
            if fila >= fila_fin:
                break
            linea = f"  fd{fd['fd']}: [{fd['tipo']}] {fd['destino']}"
            stdscr.addstr(fila, 0, linea[:ancho-1], curses.color_pair(COLOR_NORMAL)); fila += 1

    elif vista_activa == 4:
        threads = snapshot.get('threads', {}).get(pid, [])
        stdscr.addstr(fila, 0, f"Threads: {len(threads)}", curses.color_pair(COLOR_NORMAL)); fila += 1
        for t in threads:
            if fila >= fila_fin:
                break
            linea = f"  TID {t['tid']}: {t['nombre']} [{t['estado']}]"
            stdscr.addstr(fila, 0, linea[:ancho-1], color_por_estado(t['estado'])); fila += 1

    elif vista_activa == 5:
        senales = snapshot.get('senales', {}).get(pid, {})
        for categoria, lista in senales.items():
            if fila >= fila_fin:
                break
            if lista:
                stdscr.addstr(fila, 0,
                    f"{categoria}: {', '.join(lista)}"[:ancho-1],
                    curses.color_pair(COLOR_NORMAL)); fila += 1

    elif vista_activa == 6:
        datos = snapshot.get('scheduling', {}).get(pid, {})
        if datos:
            stdscr.addstr(fila, 0, f"Politica:     {datos.get('politica', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"Prioridad:    {datos.get('prioridad', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"Nice:         {datos.get('nice', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"CPUs allowed: {datos.get('cpus_allowed', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"Vol ctx sw:   {datos.get('voluntary_ctx', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1
            stdscr.addstr(fila, 0, f"Invol ctx sw: {datos.get('involuntary_ctx', '?')}", curses.color_pair(COLOR_NORMAL)); fila += 1


def dibujar_ayuda(stdscr, fila, altura, ancho):
    ayuda = [
        "TECLAS DISPONIBLES",
        "",
        "1-7 / r m f t s p g  Cambiar vista",
        "Flecha arriba/abajo  Navegar lista de procesos",
        "+                    Aumentar intervalo de la vista activa",
        "-                    Disminuir intervalo de la vista activa",
        "h / ?                Mostrar/ocultar esta ayuda",
        "q                    Salir",
        "",
        "SEÑALES (desde otra terminal):",
        "SIGUSR1  Dump del snapshot a src/dump_<timestamp>.json",
        "SIGHUP   Recargar config.json en runtime",
        "SIGUSR2  Activar/desactivar modo verbose",
    ]
    for linea in ayuda:
        if fila >= altura - 1:
            break
        stdscr.addstr(fila, 0, linea[:ancho-1], curses.color_pair(COLOR_NORMAL))
        fila += 1


def dibujar_sistema(stdscr, snapshot, fila, altura, ancho):
    datos = snapshot.get('sistema', {})
    if not datos:
        stdscr.addstr(fila, 0, "Cargando datos del sistema...",
                      curses.color_pair(COLOR_NORMAL))
        return fila

    stdscr.addstr(fila, 0, f"Uptime: {datos['uptime']}", curses.color_pair(COLOR_NORMAL)); fila += 1
    stdscr.addstr(fila, 0, f"CPU uso: {datos['cpu_uso']}%", curses.color_pair(COLOR_RUNNING)); fila += 1
    stdscr.addstr(fila, 0,
        f"Load average: {datos['load_avg1']} {datos['load_avg5']} {datos['load_avg15']}",
        curses.color_pair(COLOR_NORMAL)); fila += 1
    stdscr.addstr(fila, 0, f"Procesos activos: {datos['procesos']}",
                  curses.color_pair(COLOR_NORMAL)); fila += 2

    stdscr.addstr(fila, 0, "--- MEMORIA ---", curses.color_pair(COLOR_SEPARADOR)); fila += 1
    stdscr.addstr(fila, 0, f"Total:      {datos['mem_total']}", curses.color_pair(COLOR_NORMAL)); fila += 1
    stdscr.addstr(fila, 0, f"Libre:      {datos['mem_libre']}", curses.color_pair(COLOR_NORMAL)); fila += 1
    stdscr.addstr(fila, 0, f"Disponible: {datos['mem_disponible']}", curses.color_pair(COLOR_NORMAL)); fila += 1
    stdscr.addstr(fila, 0, f"Buffers:    {datos['buffers']}", curses.color_pair(COLOR_NORMAL)); fila += 1
    stdscr.addstr(fila, 0, f"Cached:     {datos['cached']}", curses.color_pair(COLOR_NORMAL)); fila += 1
    stdscr.addstr(fila, 0, f"Swap total: {datos['swap_total']}", curses.color_pair(COLOR_NORMAL)); fila += 1
    stdscr.addstr(fila, 0, f"Swap libre: {datos['swap_libre']}", curses.color_pair(COLOR_NORMAL)); fila += 1

    return fila