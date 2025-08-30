from pydantic import BaseModel, condecimal
from typing import Annotated
from decimal import Decimal


class OrderSchema(BaseModel):
    preco: Annotated[Decimal, condecimal(gt=0)]

    class Config:
        from_attributes = True


class OrderOutSchema(BaseModel):
    pedido_id: int
    status: str
    usuario_id: int
    preco: Decimal

    class Config:
        from_attributes = True
