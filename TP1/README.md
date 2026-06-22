# TP1 - Monitor de Procesos y Threads

**Computación II — Universidad de Mendoza — 2026**

## Descripción

Monitor de procesos en tiempo real para Linux, similar a `htop`, que muestra la anatomía interna de cada proceso leyendo directamente desde `/proc`. Implementado como un sistema multiproceso en Python 3.11 corriendo dentro de un contenedor Docker.

## Requisitos

- Docker
- docker compose

No se requiere ninguna instalación adicional en la máquina host.

## Cómo ejecutar

```bash
docker compose run --rm monitor
```

> **Nota:** usar `docker compose run` en vez de `docker compose up` porque `curses` requiere una terminal interactiva real (pty) que `up` no asigna correctamente en algunos entornos.

## Teclas

| Tecla | Acción |
|-------|--------|
| `1` / `r` | Vista Resumen |
| `2` / `m` | Vista Memoria |
| `3` / `f` | Vista File Descriptors |
| `4` / `t` | Vista Threads |
| `5` / `s` | Vista Señales |
| `6` / `p` | Vista Scheduling |
| `7` / `g` | Vista Sistema Global |
| `q` | Salir |

## Arquitectura

El sistema está compuesto por múltiples procesos corriendo en paralelo:

- **Recolector**: lista los PIDs activos leyendo `/proc` cada 1 segundo
- **7 Analizadores**: cada uno extrae una dimensión específica de cada proceso, con su propio intervalo de refresco configurable
- **Display**: renderiza la vista activa en pantalla usando `curses`
- **Manejador de señales**: captura SIGINT y SIGTERM para un shutdown limpio

Todos los componentes se comunican a través de memoria compartida (`multiprocessing.Manager`) — una lista compartida de PIDs y un diccionario compartido de snapshots.

Recolector → pids (Manager.list)
↓
7 Analizadores en paralelo
↓
snapshot (Manager.dict)
↓
Display (TUI)

## Decisiones de diseño

**¿Por qué `multiprocessing` y no `threading`?**
Python tiene el GIL (Global Interpreter Lock), que impide que dos threads ejecuten código Python al mismo tiempo. Como cada analizador hace trabajo intensivo de lectura de `/proc`, usar threads no daría paralelismo real. Con `multiprocessing` cada analizador corre en su propio proceso con su propia memoria, logrando paralelismo real a nivel del sistema operativo.

**¿Por qué `curses` y no `rich`?**
`curses` es una librería de bajo nivel que da control directo sobre cada pixel de la pantalla. Aunque requiere más trabajo que `rich`, se alinea mejor con el espíritu de la materia (entender cómo funcionan las cosas por dentro) y no requiere instalar ninguna dependencia externa — viene en la librería estándar de Python.

**¿Por qué `Manager.dict` para el snapshot?**
Cada proceso tiene su propia memoria aislada (por el modelo de fork del SO). Un diccionario normal de Python no es visible entre procesos. `Manager.dict` crea un diccionario que vive en un proceso auxiliar y es accesible desde cualquier otro proceso que tenga la referencia, usando comunicación interna por sockets/pipes.

**¿Por qué `time.sleep()` en vez de `Event.wait()` en el loop principal?**
`Event.wait()` con bloqueo indefinido puede quedar colgado cuando una señal interrumpe la llamada bloqueante a nivel del sistema operativo. Usar `while not evento.is_set(): time.sleep(0.2)` es más robusto porque `.is_set()` es una simple lectura de variable sin locks, y `time.sleep()` se interrumpe limpiamente ante señales.

## Configuración

Los intervalos de refresco de cada analizador se configuran en `config.json`:

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

## Estructura del proyecto
TP1/
├── Dockerfile
├── docker-compose.yml
├── config.json
├── requirements.txt
├── README.md
├── dudas.md
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

## Autor
Sebastián Merino — Computación II 2026
