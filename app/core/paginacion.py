from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginacionSalida(BaseModel, Generic[T]):
    datos: list[T]
    total: int
    pagina: int
    limite: int
    total_paginas: int