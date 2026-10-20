# src/mediciones.py - Script para las 3 mediciones obligatorias

import asyncio
import time
import aiohttp
import httpx


API = "http://localhost:8000"

# URLs para las mediciones de descarga
URLS_TEST = [
    "https://httpbin.org/get",
    "https://httpbin.org/ip",
    "https://httpbin.org/uuid",
    "https://httpbin.org/user-agent",
    "https://httpbin.org/headers",
]


async def crear_tarea(session: httpx.AsyncClient, tipo: str, parametros: dict, timeout: float = 30.0) -> str:
    resp = await session.post(f"{API}/tareas", json={
        "tipo": tipo,
        "parametros": parametros,
        "timeout": timeout
    })
    return resp.json()["id"]


async def esperar_tarea(session: httpx.AsyncClient, tarea_id: str) -> dict:
    while True:
        resp = await session.get(f"{API}/tareas/{tarea_id}")
        data = resp.json()
        if data["estado"] in ("completada", "fallida", "cancelada"):
            return data
        await asyncio.sleep(0.1)


# ─── Medicion 1: Concurrencia I/O ───────────────────────────────────────────

async def medicion_1():
    print("\n=== MEDICION 1: Concurrencia I/O ===")
    print("20 descargas secuenciales vs 20 concurrentes\n")

    urls = URLS_TEST * 4  # 20 URLs

    async with httpx.AsyncClient() as session:

        # Secuencial: una tarea por URL, esperamos cada una antes de la siguiente
        print("Secuencial...")
        inicio = time.time()
        for url in urls:
            tid = await crear_tarea(session, "descargar", {"urls": [url]})
            await esperar_tarea(session, tid)
        tiempo_sec = round(time.time() - inicio, 2)
        print(f"  Tiempo secuencial: {tiempo_sec}s")

        # Concurrente: una sola tarea con todas las URLs
        print("Concurrente...")
        inicio = time.time()
        tid = await crear_tarea(session, "descargar", {"urls": urls})
        await esperar_tarea(session, tid)
        tiempo_conc = round(time.time() - inicio, 2)
        print(f"  Tiempo concurrente: {tiempo_conc}s")

        speedup = round(tiempo_sec / tiempo_conc, 2)
        print(f"  Speedup: {speedup}x")


# ─── Medicion 2: Event loop bloqueado ────────────────────────────────────────

async def medicion_2():
    print("\n=== MEDICION 2: Event loop bloqueado ===")
    print("Tiempo de respuesta de GET /tareas durante una tarea CPU-bound\n")

    async with httpx.AsyncClient() as session:

        # Con executor (correcto)
        print("CON run_in_executor...")
        tid = await crear_tarea(session, "hashear", {"texto": "test", "iteraciones": 5000000}, timeout=60)

        tiempos = []
        for _ in range(5):
            inicio = time.time()
            await session.get(f"{API}/tareas")
            tiempos.append(round(time.time() - inicio, 3))
            await asyncio.sleep(0.2)

        await esperar_tarea(session, tid)
        print(f"  Tiempos de GET /tareas: {tiempos}")
        print(f"  Promedio: {round(sum(tiempos)/len(tiempos), 3)}s")


# ─── Medicion 3: Techo del pool ──────────────────────────────────────────────

async def medicion_3():
    print("\n=== MEDICION 3: Techo del pool ===")
    print("Subiendo tareas concurrentes hasta degradar tiempos\n")

    async with httpx.AsyncClient() as session:
        for cantidad in [1, 5, 10, 20, 50]:
            ids = []
            inicio = time.time()

            # Crear todas las tareas de golpe
            for _ in range(cantidad):
                tid = await crear_tarea(session, "esperar", {"segundos": 2})
                ids.append(tid)

            # Esperar que todas terminen
            await asyncio.gather(*[esperar_tarea(session, tid) for tid in ids])
            tiempo = round(time.time() - inicio, 2)

            print(f"  {cantidad} tareas de 2s: tardó {tiempo}s (ideal: 2s con pool infinito)")


async def main():
    await medicion_1()
    await medicion_2()
    await medicion_3()
    print("\n=== Mediciones completadas ===")


if __name__ == "__main__":
    asyncio.run(main())
