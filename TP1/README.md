# TP1 - Monitor de Procesos y Threads

**Computación II — Universidad de Mendoza — 2026**  
**Autor:** Sebastián Merino

---

## Descripción

Monitor de procesos en tiempo real para Linux, similar a `htop`, que muestra la anatomía interna de cada proceso leyendo directamente desde `/proc`. Implementado como un sistema multiproceso en Python 3.11 corriendo dentro de un contenedor Docker.

No se permite el uso de `psutil` ni equivalentes — toda la información se extrae leyendo `/proc` directamente.

---

## Requisitos

- Docker
- docker compose

No se requiere ninguna instalación adicional en la máquina host. Todo el entorno corre dentro del contenedor.

---

## Cómo ejecutar

```bash
docker compose run --rm monitor
```

> **Nota:** se usa `docker compose run` en vez de `docker compose up` porque `curses` requiere una terminal interactiva real (pty) que `up` no asigna correctamente en algunos entornos.

---

## Teclas

| Tecla | Acción |
|-------|--------|
| `1` / `r` | Vista Resumen (PID, PPID, nombre, estado, threads, CPU%) |
| `2` / `m` | Vista Memoria (VmRSS, VmSize, VmSwap, segmentos text/data/heap/stack) |
| `3` / `f` | Vista File Descriptors (lista de FDs y sus destinos) |
| `4` / `t` | Vista Threads (LWPs con estado) |
| `5` / `s` | Vista Señales (bloqueadas, ignoradas, capturadas, pendientes) |
| `6` / `p` | Vista Scheduling (prioridad, nice, política, context switches) |
| `7` / `g` | Vista Sistema Global (CPU, memoria, load average, uptime) |
| `+` / `-` | Aumentar / disminuir intervalo de la vista activa |
| `q` | Salir con shutdown limpio |

---

## Señales soportadas

| Señal | Acción |
|-------|--------|
| `SIGINT` (Ctrl+C) | Shutdown limpio de todos los procesos |
| `SIGTERM` | Shutdown limpio de todos los procesos |
| `SIGUSR1` | Dump del snapshot actual a un archivo JSON en `src/dump_<timestamp>.json` |
| `SIGHUP` | Recarga `config.json` y actualiza los intervalos de todos los analizadores en runtime |
| `SIGUSR2` | Activa/desactiva modo verbose |

### Cómo usar las señales

Con el monitor corriendo, desde otra terminal:

```bash
# Ver el nombre del contenedor
docker ps

# Mandar cualquier señal al proceso principal (PID 1 dentro del contenedor)
docker exec <nombre_contenedor> python3 -c "import os, signal; os.kill(1, signal.SIGUSR1)"
docker exec <nombre_contenedor> python3 -c "import os, signal; os.kill(1, signal.SIGHUP)"
docker exec <nombre_contenedor> python3 -c "import os, signal; os.kill(1, signal.SIGUSR2)"
```

---

## Configuración

Los intervalos de refresco de cada analizador se configuran en `config.json`. Se pueden cambiar en runtime mandando SIGHUP después de editar el archivo:

```json
{
    "intervalos": {
        "recolector": 1,
        "resumen": 2,
        "memoria": 3,
        "threads": 2,
        "fds": 5,
        "senales": 10,
        "scheduling": 10,
        "sistema": 2
    },
    "display": {
        "intervalo": 0.5
    }
}
```

---

## Arquitectura

El sistema está compuesto por múltiples procesos corriendo en paralelo:
Recolector (cada 1s)
│
▼
pids (Manager.list compartida)
│
├──► Analizador Resumen (cada 2s) ──┐
├──► Analizador Memoria (cada 3s) ──┤
├──► Analizador Threads (cada 2s) ──┤
├──► Analizador FDs (cada 5s) ──┼──► snapshot (Manager.dict)
├──► Analizador Señales (cada 10s) ──┤ │
├──► Analizador Scheduling (cada 10s) ──┤ │
└──► Analizador Sistema (cada 2s) ──┘ │
▼
Display TUI
(cada 0.5s)


Cada componente es un **proceso independiente** (`multiprocessing.Process`), no un thread. La comunicación entre ellos usa:
- `Manager.list()` para la lista de PIDs activos
- `Manager.dict()` para el snapshot global de datos
- `multiprocessing.Value('d', ...)` para los intervalos modificables en runtime

---

## Decisiones de diseño

**¿Por qué `multiprocessing` y no `threading`?**  
Python tiene el GIL (Global Interpreter Lock), que impide que dos threads ejecuten código Python al mismo tiempo. Como cada analizador hace trabajo intensivo de lectura de `/proc`, usar threads no daría paralelismo real. Con `multiprocessing` cada analizador corre en su propio proceso con su propia memoria, logrando paralelismo real a nivel del sistema operativo.

**¿Por qué `curses` y no `rich`?**  
`curses` es una librería de bajo nivel que da control directo sobre la pantalla. Se alinea mejor con el espíritu de la materia (entender cómo funcionan las cosas por dentro) y no requiere instalar ninguna dependencia externa — viene en la librería estándar de Python.

**¿Por qué `Manager.dict` para el snapshot?**  
Cada proceso tiene su propia memoria aislada por el modelo de fork del SO. Un diccionario normal de Python no es visible entre procesos. `Manager.dict` crea un diccionario que vive en un proceso auxiliar y es accesible desde cualquier otro proceso que tenga la referencia.

**¿Por qué `multiprocessing.Value` para los intervalos?**  
A diferencia de un entero normal (que tras el fork es una copia privada de cada proceso), `Value` usa `mmap` con `MAP_SHARED` — reserva un segmento de memoria compartida real al que todos los procesos apuntan a la misma dirección física. Esto permite que el display modifique el intervalo de un analizador con `+`/`-` y que ese cambio sea inmediatamente visible en el proceso del analizador.

**¿Por qué los handlers de señales solo prenden flags?**  
Los handlers de señales corren en un contexto asíncrono donde casi ninguna operación es segura (no se puede hacer I/O, no se pueden tomar locks). El patrón correcto es que el handler solo modifique una variable simple (`_flag = True`) y que el loop principal haga el trabajo real (escribir el dump, recargar el config).

**¿Por qué `time.sleep()` en vez de `Event.wait()` en el loop principal?**  
`Event.wait()` con bloqueo indefinido puede quedar colgado cuando una señal interrumpe la llamada bloqueante a nivel del sistema operativo en contenedores Docker. Usar `while not evento.is_set(): time.sleep(0.2)` es más robusto porque `.is_set()` es una simple lectura de variable sin locks.

**¿Por qué `stdscr.timeout(100)` en vez de `nodelay(True)` + `sleep`?**  
`timeout(100)` hace que `getch()` espere hasta 100ms por una tecla antes de retornar `-1`. Esto permite que el teclado responda en menos de 100ms sin consumir CPU innecesariamente, a diferencia de `nodelay(True)` + `time.sleep(0.5)` que introduce hasta 500ms de latencia en la respuesta al teclado.

---

## Conceptos del curso aplicados

**Procesos vs Threads**  
El sistema usa 9 procesos independientes (recolector + 7 analizadores + display). Cada uno tiene su propio espacio de memoria, su propio PID y su propio scheduling por parte del kernel. Esto es visible en la propia vista Resumen del monitor: se pueden ver los 9 procesos con sus PIDs y estados.

**fork() y Copy-on-Write**  
Cuando `multiprocessing.Process.start()` crea un hijo, internamente hace un `fork()`. El hijo hereda una copia del espacio de memoria del padre, incluyendo los handlers de señales registrados — por eso es importante registrar los handlers *antes* de crear los procesos hijos, para que hereden el comportamiento correcto.

**Memoria compartida con mmap**  
`multiprocessing.Value` usa `mmap` con `MAP_SHARED` por debajo — reserva una página de memoria que el kernel mapea en el espacio de direcciones de todos los procesos que tienen la referencia. Escribir `.value` desde el display es escribir en la misma dirección física que el analizador lee.

**IPC con Manager**  
`Manager.dict()` y `Manager.list()` implementan IPC a través de un proceso servidor que serializa los accesos concurrentes. Internamente usa sockets/pipes para que los procesos clientes lean y escriban datos de forma segura sin race conditions.

**Señales**  
El monitor maneja 5 señales: SIGINT y SIGTERM para shutdown limpio, SIGUSR1 para dump, SIGHUP para reload de config, y SIGUSR2 para modo verbose. Los handlers siguen el principio de async-signal-safety: solo prenden flags, el trabajo real lo hace el loop principal.

**Estados de proceso**  
La vista Resumen muestra el estado de cada proceso (R/S/D/T/Z) leído del campo 3 de `/proc/<pid>/stat`. Los procesos en estado R aparecen en verde y los zombies en rojo.

**Scheduling**  
La vista Scheduling muestra la política (NORMAL/FIFO/RR/BATCH/IDLE), prioridad, nice y context switches voluntarios e involuntarios de cada proceso, leídos de `/proc/<pid>/stat` y `/proc/<pid>/status`.

---

## Limitaciones conocidas

- **El monitor solo ve los procesos dentro del contenedor Docker**, no los del sistema host. Esto es consecuencia del namespace de PIDs de Docker — desde adentro del contenedor, `/proc` solo expone los procesos del propio contenedor.
- **El CPU% tiene una imprecisión en la primera vuelta** de cada analizador porque no hay lectura anterior con la que calcular el delta — se muestra `0.0` hasta que el analizador completa su primer ciclo.
- **`docker compose up` no funciona correctamente** para este monitor porque `curses` requiere una terminal interactiva real (pty). Hay que usar `docker compose run --rm monitor`.
- **El modo verbose (SIGUSR2)** está implementado a nivel de señal pero su efecto visual en el display está pendiente de completar.

---

## Cómo correr los tests

```bash
docker compose run --rm monitor python tests/test_procfs.py
```

---

## Estructura del proyecto
TP1/
├── Dockerfile
├── docker-compose.yml
├── config.json
├── requirements.txt
├── README.md
└── src/
├── main.py
├── recolector.py
├── procfs.py
├── display.py
├── senales.py
└── analizadores/
├── resumen.py
├── memoria.py
├── threads.py
├── fds.py
├── senales.py
├── scheduling.py
└── sistema.py
└── tests/
└── test_procfs.py