import asyncio
import hashlib
import time
import aiohttp


async def ejecutar_descargar(parametros: dict) -> dict:
    urls = parametros.get("urls", [])
    resultados = []

    async with aiohttp.ClientSession() as session:
        async def descargar_una(url: str) -> dict:
            inicio = time.time()
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    contenido = await resp.read()
                    return {
                        "url": url,
                        "status": resp.status,
                        "tamanio_bytes": len(contenido),
                        "tiempo_segundos": round(time.time() - inicio, 2)
                    }
            except Exception as e:
                return {
                    "url": url,
                    "error": str(e),
                    "tiempo_segundos": round(time.time() - inicio, 2)
                }

        resultados = await asyncio.gather(*[descargar_una(url) for url in urls])

    return {"descargas": list(resultados)}


async def ejecutar_hashear(parametros: dict, loop: asyncio.AbstractEventLoop) -> dict:
    texto = parametros.get("texto", "")
    iteraciones = parametros.get("iteraciones", 1000)

    def hashear_sync():
        datos = texto.encode()
        for _ in range(iteraciones):
            datos = hashlib.sha256(datos).digest()
        return datos.hex()

    # Corre en executor para no bloquear el event loop
    resultado = await loop.run_in_executor(None, hashear_sync)
    return {"hash": resultado, "iteraciones": iteraciones}


async def ejecutar_esperar(parametros: dict) -> dict:
    segundos = parametros.get("segundos", 1)
    await asyncio.sleep(segundos)
    return {"dormido_segundos": segundos}
