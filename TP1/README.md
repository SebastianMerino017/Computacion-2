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
| `2` / `m` | Vista Memoria (VmRSS, VmSize, VmSwap) |
| `3` / `f` | Vista File Descriptors (lista de FDs y sus destinos) |
| `4` / `t` | Vista Threads (LWPs con estado) |
| `5` / `s` | Vista Señales (bloqueadas, ignoradas, capturadas, pendientes) |
| `6` / `p` | Vista Scheduling (prioridad, nice, política, context switches) |
| `7` / `g` | Vista Sistema Global (CPU, memoria, load average, uptime) |
| `q` | Salir con shutdown limpio |
---
## Señales soportadas

| Señal | Acción |
|-------|--------|
| `SIGINT` (Ctrl+C) | Shutdown limpio de todos los procesos |
| `SIGTERM` | Shutdown limpio de todos los procesos |
| `SIGUSR1` | Dump del snapshot actual a un archivo JSON |
### Cómo usar SIGUSR1
Con el monitor corriendo, desde otra terminal:

```bash
# Ver el nombre del contenedor
docker ps

# Mandar SIGUSR1 al proceso principal (PID 1 dentro del contenedor)
docker exec <nombre_contenedor> python3 -c "import os, signal; os.kill(1, signal.SIGUSR1)"

# Ver el archivo generado
ls src/dump_*.json
cat src/dump_<timestamp>.json
```
---
## Configuración
Los intervalos de refresco de cada analizador se configuran en `config.json` sin necesidad de tocar el código:
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
├──► Analizador Resumen    (cada 2s)  ──┐
├──► Analizador Memoria    (cada 3s)  ──┤
├──► Analizador Threads    (cada 2s)  ──┤
├──► Analizador FDs        (cada 5s)  ──┼──► snapshot (Manager.dict)
├──► Analizador Señales    (cada 10s) ──┤         │
├──► Analizador Scheduling (cada 10s) ──┤         │
└──► Analizador Sistema    (cada 2s)  ──┘         │
▼
Display TUI
(cada 0.5s)
Cada componente es un **proceso independiente** (`multiprocessing.Process`), no un thread. La comunicación entre ellos usa:
- `Manager.list()` para la lista de PIDs activos
- `Manager.dict()` para el snapshot global de datos

---
## Decisiones de diseño
**¿Por qué `multiprocessing` y no `threading`?**  
Python tiene el GIL (Global Interpreter Lock), que impide que dos threads ejecuten código Python al mismo tiempo. Como cada analizador hace trabajo intensivo de lectura de `/proc`, usar threads no daría paralelismo real. Con `multiprocessing` cada analizador corre en su propio proceso con su propia memoria, logrando paralelismo real a nivel del sistema operativo.

**¿Por qué `curses` y no `rich`?**  
`curses` es una librería de bajo nivel que da control directo sobre la pantalla. Se alinea mejor con el espíritu de la materia (entender cómo funcionan las cosas por dentro) y no requiere instalar ninguna dependencia externa — viene en la librería estándar de Python.

**¿Por qué `Manager.dict` para el snapshot?**  
Cada proceso tiene su propia memoria aislada por el modelo de fork del SO. Un diccionario normal de Python no es visible entre procesos. `Manager.dict` crea un diccionario que vive en un proceso auxiliar y es accesible desde cualquier otro proceso que tenga la referencia.

**¿Por qué `time.sleep()` en vez de `Event.wait()` en el loop principal?**  
`Event.wait()` con bloqueo indefinido puede quedar colgado cuando una señal interrumpe la llamada bloqueante a nivel del sistema operativo en ciertos entornos (como contenedores Docker). Usar `while not evento.is_set(): time.sleep(0.2)` es más robusto porque `.is_set()` es una simple lectura de variable sin locks.

**¿Por qué `configurar_handlers()` antes de crear el `Manager`?**  
El proceso del Manager se crea con `fork()` y hereda los handlers de señales del padre. Si registramos los handlers después de crear el Manager, ese proceso hereda el comportamiento default de Python ante SIGINT (que lo mata de golpe), dejando colgados a los demás procesos que intentan acceder al diccionario compartido.
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