from pydantic import BaseModel, confloat, Field
from typing import Annotated


class OrderSchema(BaseModel):
    preco: Annotated[confloat(gt=0), Field(example=0)]

    class Config:
        from_attributes = True


class OrderOutSchema(BaseModel):
    pedido_id: int
    status: str
    usuario_id: int
    preco: float

    class Config:
        from_attributes = True
