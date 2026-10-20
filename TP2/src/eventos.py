import asyncio
from typing import Set
from fastapi import WebSocket


class GestorEventos:
    def __init__(self):
        self.conexiones: Set[WebSocket] = set()

    async def conectar(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.conexiones.add(websocket)

    def desconectar(self, websocket: WebSocket) -> None:
        self.conexiones.discard(websocket)

    async def notificar(self, mensaje: dict) -> None:
        if not self.conexiones:
            return
        desconectadas = set()
        for ws in self.conexiones:
            try:
                await ws.send_json(mensaje)
            except Exception:
                desconectadas.add(ws)
        self.conexiones -= desconectadas


# Instancia global compartida
gestor_eventos = GestorEventos()
