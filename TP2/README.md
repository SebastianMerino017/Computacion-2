# TP2 - Plataforma de Tareas Distribuidas

**Computación II — Universidad de Mendoza — 2026**  
**Autor:** Sebastián Merino

---

## Descripción

Plataforma de tareas distribuidas implementada con FastAPI y asyncio. Permite encolar trabajos por HTTP, ejecutarlos de forma concurrente y consultar su estado y resultado en tiempo real.

## Cómo ejecutar

```bash
docker compose up --build
```

La API queda disponible en `http://localhost:8000`.  
Documentación interactiva en `http://localhost:8000/docs`.

---

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/tareas` | Encola una tarea. Responde inmediatamente con el ID |
| `GET` | `/tareas` | Lista todas las tareas (filtro opcional por estado) |
| `GET` | `/tareas/{id}` | Estado y resultado de una tarea |
| `DELETE` | `/tareas/{id}` | Cancela una tarea encolada o en ejecución |
| `GET` | `/estadisticas` | Totales por estado, tiempo promedio, workers ocupados |

### Estados posibles
`pendiente` → `ejecutando` → `completada` / `fallida` / `cancelada`

---

## Tipos de tarea

### descargar (I/O-bound)
```bash
curl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d "{\"tipo\": \"descargar\", \"parametros\": {\"urls\": [\"https://httpbin.org/get\", \"https://httpbin.org/ip\"]}}"
```

### hashear (CPU-bound)
```bash
curl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d "{\"tipo\": \"hashear\", \"parametros\": {\"texto\": \"hola mundo\", \"iteraciones\": 100000}}"
```

### esperar (I/O simulado)
```bash
curl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d "{\"tipo\": \"esperar\", \"parametros\": {\"segundos\": 5}}"
```

### Cancelar una tarea
```bash
curl -X DELETE http://localhost:8000/tareas/{id}
```

---

## Diagrama de arquitectura
Cliente HTTP
│
▼
┌─────────────────┐
│ API (FastAPI) │ POST /tareas → encola y responde inmediatamente
│ asyncio │ GET /tareas/{id} → consulta estado
└────────┬────────┘
│
▼
┌─────────────────┐
│ asyncio.Queue │ Cola compartida en memoria
└────────┬────────┘
│
▼
┌─────────────────────────────────┐
│ Pool de 5 workers (corrutinas) │
│ │
│ descargar → asyncio.gather │
│ esperar → asyncio.sleep │
│ hashear → run_in_executor │
└─────────────────────────────────┘


---

## Decisiones de diseño

**¿Por qué `asyncio.Queue` y no `queue.Queue`?**  
`queue.Queue` es thread-safe pero bloqueante — llamar a `.get()` detendría el event loop entero. `asyncio.Queue` es la versión asíncrona: el `await cola.get()` cede el control al event loop mientras espera, permitiendo que otros workers y endpoints sigan funcionando.

**¿Cómo evitás que una tarea CPU-bound congele la API?**  
Con `loop.run_in_executor(None, hashear_sync)`. El event loop de asyncio corre en un solo hilo; si ejecutamos código CPU-intensivo directamente, bloquea todo. `run_in_executor` delega la función a un `ThreadPoolExecutor` (o `ProcessPoolExecutor`), liberando el event loop para seguir atendiendo requests mientras el hash se calcula en otro hilo.

**¿Cómo implementaste la cancelación?**  
Cada tarea en ejecución tiene un `asyncio.Task` registrado en `almacen.tasks_asyncio`. Al recibir `DELETE /tareas/{id}`, se llama a `task.cancel()`, que inyecta un `CancelledError` en la corrutina en el próximo `await`. El `try/except CancelledError` en `procesar_tarea` captura esto, marca la tarea como `cancelada` y libera los recursos limpiamente.

**¿Qué pasa si un worker lanza una excepción no capturada?**  
El `try/except Exception` en `procesar_tarea` captura cualquier error inesperado, marca la tarea como `fallida` con el mensaje de error, y el worker continúa procesando la siguiente tarea de la cola sin caerse.

---

## Mediciones

### Medición 1: Concurrencia I/O

20 descargas a httpbin.org:

| Modo | Tiempo |
|------|--------|
| Secuencial (una por una) | 16.78s |
| Concurrente (todas juntas) | 1.33s |
| **Speedup** | **12.62x** |

Las 20 URLs descargadas concurrentemente con `asyncio.gather` tardaron lo que la más lenta, no la suma de todas. Esto confirma que asyncio es ideal para I/O-bound.

### Medición 2: Event loop bloqueado

Tiempo de respuesta de `GET /tareas` mientras corre `hashear` con 5.000.000 iteraciones:

| Modo | Tiempos de respuesta |
|------|---------------------|
| CON `run_in_executor` | [15ms, 20ms, 48ms, 15ms, 20ms] — promedio 24ms |

Con `run_in_executor` el event loop nunca se bloqueó — la API siguió respondiendo normalmente mientras el hash se calculaba en background. Sin executor, esos mismos requests habrían tardado varios segundos.

### Medición 3: Techo del pool

Pool de 5 workers, tareas de 2 segundos cada una:

| Tareas enviadas | Tiempo total | Explicación |
|-----------------|-------------|-------------|
| 1 | 2.02s | 1 ronda |
| 5 | 2.30s | 1 ronda (caben todas) |
| 10 | 4.30s | 2 rondas |
| 20 | 8.31s | 4 rondas |
| 50 | 20.32s | 10 rondas |

El techo está en los **5 workers**: cada grupo de 5 tareas ocupa una "ronda" de 2 segundos. Con más workers el techo sube; con menos, baja. El límite real está en la memoria y el overhead del event loop.

---

## Conceptos del curso aplicados

**Event loop y corrutinas (Clase 18)**  
Los workers son corrutinas que corren dentro del event loop de asyncio. El `await cola.get()` cede el control sin bloquear, igual que el mecanismo de `yield` que vimos al estudiar generadores — la corrutina se suspende y el event loop puede atender otros eventos.

**I/O Multiplexing (Clase 17)**  
`asyncio.gather` en la tarea `descargar` funciona igual que `select`/`epoll`: registra múltiples operaciones I/O y el event loop las maneja en el orden en que completan, sin dedicar un hilo a cada una.

**Productor-consumidor con cola (Clase 11)**  
El pool de workers consume de una `asyncio.Queue` compartida. Es el mismo patrón productor-consumidor pero con corrutinas en vez de threads: no hace falta lock porque el event loop no interrumpe entre `await`s — la concurrencia es cooperativa, no preemptiva.

**CPU-bound vs I/O-bound**  
`hashear` demuestra por qué asyncio no sirve para CPU-bound: el GIL y el event loop en un solo hilo significan que código que no hace `await` bloquea todo. `run_in_executor` resuelve esto delegando a un ThreadPoolExecutor que corre en paralelo real.

---

## Limitaciones conocidas

- El estado vive solo en memoria — si el contenedor se reinicia sin SIGTERM, se pierde todo
- El pool tiene 5 workers hardcodeados (configurable en `iniciar_workers`)
- La medición 2 solo muestra el caso CON executor — sin executor el event loop se bloquearía completamente
- `httpbin.org` puede ser lento o inestable, afectando los tiempos de la medición 1

---

## Lo que aprendí

Antes de este TP entendía asyncio como "algo que hace las cosas más rápidas". Ahora entiendo que la velocidad viene de no bloquear el event loop: mientras una descarga espera respuesta del servidor, el event loop puede atender otros requests o avanzar otras descargas. Es concurrencia cooperativa, no paralelismo real.

Lo más revelador fue la medición del techo del pool: ver que 10 tareas de 2 segundos tardan 4 segundos (no 2) porque el pool tiene solo 5 workers me hizo entender que el límite no es asyncio sino cuántos workers tenés. Asyncio es el mecanismo; el pool es el límite.

También entendí por qué `run_in_executor` es necesario y no solo "una optimización": sin él, una sola tarea CPU-bound congela la API entera. Con él, el event loop sigue libre. La diferencia entre los dos modos es la diferencia entre un servidor que responde y uno que no.
