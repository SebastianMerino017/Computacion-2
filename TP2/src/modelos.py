from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, field
import time
import uuid


class EstadoTarea(str, Enum):
    PENDIENTE = "pendiente"
    EJECUTANDO = "ejecutando"
    COMPLETADA = "completada"
    FALLIDA = "fallida"
    CANCELADA = "cancelada"


class TipoTarea(str, Enum):
    DESCARGAR = "descargar"
    HASHEAR = "hashear"
    ESPERAR = "esperar"


@dataclass
class Tarea:
    tipo: TipoTarea
    parametros: dict
    timeout: float = 30.0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    estado: EstadoTarea = EstadoTarea.PENDIENTE
    creada_en: float = field(default_factory=time.time)
    iniciada_en: Optional[float] = None
    finalizada_en: Optional[float] = None
    resultado: Optional[Any] = None
    error: Optional[str] = None

    def a_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "parametros": self.parametros,
            "timeout": self.timeout,
            "estado": self.estado,
            "creada_en": self.creada_en,
            "iniciada_en": self.iniciada_en,
            "finalizada_en": self.finalizada_en,
            "resultado": self.resultado,
            "error": self.error,
        }
