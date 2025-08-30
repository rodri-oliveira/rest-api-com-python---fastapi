from pydantic import BaseModel, condecimal, ConfigDict
from typing import Annotated
from decimal import Decimal


class OrderSchema(BaseModel):
    preco: Annotated[Decimal, condecimal(gt=0)]
    model_config = ConfigDict(from_attributes=True)


class OrderOutSchema(BaseModel):
    pedido_id: int
    status: str
    usuario_id: int
    preco: Decimal
    model_config = ConfigDict(from_attributes=True)
