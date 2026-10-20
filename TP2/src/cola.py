import asyncio
from typing import Dict, Optional
from src.modelos import Tarea, EstadoTarea


class AlmacenTareas:
    def __init__(self):
        self.tareas: Dict[str, Tarea] = {}
        self.cola: asyncio.Queue = asyncio.Queue()
        self.tasks_asyncio: Dict[str, asyncio.Task] = {}

    def agregar(self, tarea: Tarea) -> None:
        self.tareas[tarea.id] = tarea

    def obtener(self, id: str) -> Optional[Tarea]:
        return self.tareas.get(id)

    def listar(self, estado: Optional[EstadoTarea] = None) -> list:
        tareas = list(self.tareas.values())
        if estado:
            tareas = [t for t in tareas if t.estado == estado]
        return tareas

    def estadisticas(self) -> dict:
        tareas = list(self.tareas.values())
        totales = {e.value: 0 for e in EstadoTarea}
        tiempos = []

        for t in tareas:
            totales[t.estado.value] += 1
            if t.iniciada_en and t.finalizada_en:
                tiempos.append(t.finalizada_en - t.iniciada_en)

        return {
            "totales_por_estado": totales,
            "tiempo_promedio": round(sum(tiempos) / len(tiempos), 2) if tiempos else 0,
            "workers_ocupados": sum(
                1 for t in tareas if t.estado == EstadoTarea.EJECUTANDO
            ),
        }


# Instancia global compartida
almacen = AlmacenTareas()
