from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from fastapi import HTTPException

from models.pedido_model import Pedido, StatusPedido
from models.item_pedido_model import ItensPedido
from models.usuario_model import Usuario
from schemas.itemOrder_schema import ItemPedidoCreateSchema, ItemPedidoOutSchema


def add_item_to_order(
    *,
    session: Session,
    current_user: Usuario,
    order_id: int,
    item_data: ItemPedidoCreateSchema,
) -> ItensPedido:
    """
    Regras de negócio para adicionar um item ao pedido:
    - Pedido deve existir
    - Permissão: admin ou dono do pedido
    - Não permitir quando status == CANCELADO
    - Calcular subtotal no servidor quando ausente
    - Atualizar o total do pedido (preco) incrementalmente
    """
    pedido = (
        session.query(Pedido)
        .filter(Pedido.pedido_id == order_id)
        .first()
    )
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    if not (current_user.admin or pedido.usuario_id == current_user.usuario_id):
        raise HTTPException(status_code=403, detail="Sem permissão para adicionar item neste pedido")

    if pedido.status == StatusPedido.CANCELADO:
        raise HTTPException(status_code=409, detail="Não é possível adicionar itens a um pedido cancelado")

    # Sempre calcular subtotal no servidor para evitar manipulação do cliente
    if item_data.quantidade < 1:
        raise HTTPException(status_code=422, detail="Quantidade deve ser >= 1")
    if item_data.preco_unitario <= 0:
        raise HTTPException(status_code=422, detail="Preço unitário deve ser > 0")
    subtotal = item_data.quantidade * item_data.preco_unitario

    novo_item = ItensPedido(
        pedido_id=order_id,
        nome_produto=item_data.nome_produto,
        quantidade=item_data.quantidade,
        preco_unitario=item_data.preco_unitario,
        subtotal=subtotal,
    )
    session.add(novo_item)

    # Garante que o item esteja visível na transação para agregação
    session.flush()
    # Recalcula o total do pedido diretamente no banco (evita drift e cache)
    total = (
        session.query(func.sum(ItensPedido.subtotal))
        .filter(ItensPedido.pedido_id == order_id)
        .scalar()
    )
    if total is None:
        total = Decimal("0.00")
    pedido.preco = total
    session.add(pedido)

    session.commit()
    session.refresh(novo_item)
    return novo_item
