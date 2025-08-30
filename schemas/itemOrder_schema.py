from pydantic import BaseModel, conint, condecimal, ConfigDict
from typing import Annotated
from decimal import Decimal

class ItemPedidoCreateSchema(BaseModel):
    # pedido_id não é necessário se vier na rota (ex.: /orders/{order_id}/add-item)
    nome_produto: str
    quantidade: Annotated[int, conint(ge=1)]
    preco_unitario: Annotated[Decimal, condecimal(gt=0)]

    model_config = ConfigDict(from_attributes=True)

class ItemPedidoOutSchema(BaseModel):
    id: int
    pedido_id: int
    nome_produto: str
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)