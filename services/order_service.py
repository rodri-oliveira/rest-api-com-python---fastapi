from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from fastapi import HTTPException

from models.pedido_model import Pedido, StatusPedido
from models.item_pedido_model import ItensPedido
from models.usuario_model import Usuario
from schemas.itemOrder_schema import ItemPedidoCreateSchema, ItemPedidoOutSchema


def _get_order_or_404(session: Session, order_id: int) -> Pedido:
    pedido = (
        session.query(Pedido)
        .filter(Pedido.pedido_id == order_id)
        .first()
    )
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido


def _assert_order_permission(current_user: Usuario, pedido: Pedido, action: str) -> None:
    if not (current_user.admin or pedido.usuario_id == current_user.usuario_id):
        raise HTTPException(status_code=403, detail=f"Sem permissão para {action} neste pedido")


def _assert_order_modifiable(pedido: Pedido, action: str) -> None:
    # Restringe operações de modificação em estados finais
    if pedido.status in {StatusPedido.CANCELADO, StatusPedido.ENTREGUE}:
        raise HTTPException(status_code=409, detail=f"Não é possível {action} em um pedido {pedido.status.value}")


def _recalc_order_total(session: Session, order_id: int) -> Decimal:
    total = (
        session.query(func.sum(ItensPedido.subtotal))
        .filter(ItensPedido.pedido_id == order_id)
        .scalar()
    )
    return total if total is not None else Decimal("0.00")


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
    pedido = _get_order_or_404(session, order_id)
    _assert_order_permission(current_user, pedido, "adicionar item")
    _assert_order_modifiable(pedido, "adicionar itens")

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
    pedido.preco = _recalc_order_total(session, order_id)
    session.add(pedido)

    session.commit()
    session.refresh(novo_item)
    return novo_item


def remove_item_from_order(
    *,
    session: Session,
    current_user: Usuario,
    order_id: int,
    item_id: int,
) -> ItemPedidoOutSchema:
    """
    Remove um item de um pedido com regras de negócio:
    - Pedido deve existir
    - Permissão: admin ou dono do pedido
    - Não permitir quando status == CANCELADO
    - Recalcula o total do pedido após remoção
    """
    pedido = _get_order_or_404(session, order_id)
    _assert_order_permission(current_user, pedido, "remover item")
    _assert_order_modifiable(pedido, "remover itens")

    item = (
        session.query(ItensPedido)
        .filter(ItensPedido.id == item_id, ItensPedido.pedido_id == order_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item do pedido não encontrado")

    # Captura dados para retorno antes da deleção (como tipos nativos)
    removed_data = {
        "id": int(item.id),
        "pedido_id": int(item.pedido_id),
        "nome_produto": str(item.nome_produto),
        "quantidade": int(item.quantidade),
        # Garante materialização segura de Numeric -> Decimal
        "preco_unitario": Decimal(str(item.preco_unitario)),
        "subtotal": Decimal(str(item.subtotal)),
    }

    # Deleta via query para evitar problemas de estado da instância deletada
    (
        session.query(ItensPedido)
        .filter(ItensPedido.id == item_id, ItensPedido.pedido_id == order_id)
        .delete(synchronize_session=False)
    )
    session.flush()

    # Recalcula o total do pedido diretamente no banco
    pedido.preco = _recalc_order_total(session, order_id)
    session.add(pedido)

    session.commit()
    return ItemPedidoOutSchema(**removed_data)
