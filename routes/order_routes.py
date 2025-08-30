from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.dependencies import get_session, get_current_user
from schemas.order_schema import OrderSchema, OrderOutSchema
from models.pedido_model import Pedido
from models.usuario_model import Usuario
from fastapi import HTTPException
from models.pedido_model import StatusPedido
from models.item_pedido_model import ItensPedido
from schemas.itemOrder_schema import ItemPedidoCreateSchema, ItemPedidoOutSchema
from services.order_service import add_item_to_order as svc_add_item
from services.order_service import remove_item_from_order as svc_remove_item


order_router = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(get_current_user)])

@order_router.get("/list", response_model=list[OrderOutSchema])
async def list_orders(
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
    all: bool = False,
):
    """
    Lista pedidos do usuário autenticado.
    - Se `all=true` e for admin: lista todos os pedidos.
    - Se `all=true` e NÃO for admin: 403.
    - Caso contrário: lista apenas pedidos do usuário atual.
    Retorna 404 se não houver pedidos conforme o filtro.
    """
    try:
        if all:
            if not current_user.admin:
                raise HTTPException(status_code=403, detail="Sem permissão para listar todos os pedidos")
            pedidos = session.query(Pedido).all()
        else:
            pedidos = (
                session.query(Pedido)
                .filter(Pedido.usuario_id == current_user.usuario_id)
                .all()
            )

        if not pedidos:
            raise HTTPException(status_code=404, detail="Nenhum pedido encontrado")

        return pedidos
    except HTTPException:
        # Propaga erros de autorização/negócio
        raise
    except Exception:
        # Erro interno (DB, etc.)
        raise HTTPException(status_code=500, detail="Erro ao listar pedidos. Tente novamente mais tarde.")
    

@order_router.get("/my", response_model=list[OrderOutSchema])
async def list_my_orders(
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista todos os pedidos do usuário autenticado.
    Retorna 404 se não houver pedidos.
    """
    try:
        pedidos = (
            session.query(Pedido)
            .filter(Pedido.usuario_id == current_user.usuario_id)
            .all()
        )
        if not pedidos:
            raise HTTPException(status_code=404, detail="Nenhum pedido encontrado")
        return pedidos
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao listar pedidos do usuário. Tente novamente mais tarde.")

@order_router.post("", response_model=OrderOutSchema)
async def create_order(order_schema: OrderSchema, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    """
    Cria um novo pedido (requer AccessToken)
    """
    # Cria pedido para o usuário autenticado
    # TODO: migrar para modelo baseado em itens de pedido (produto_id, quantidade) e calcular o total no servidor.
    # O campo 'preco' vindo do cliente é uma simplificação didática e será removido em refator futura.
    new_order = Pedido(current_user.usuario_id, order_schema.preco)
    session.add(new_order)
    session.commit()
    session.refresh(new_order)
    return new_order

@order_router.get("/{order_id}", response_model=OrderOutSchema)
async def get_order_by_id(order_id: int, session: Session = Depends(get_session)):
    """
    Retorna um pedido pelo ID (requer AccessToken)
    """
    pedido = session.query(Pedido).filter(Pedido.pedido_id == order_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido

@order_router.delete("/{order_id}", response_model=OrderOutSchema)
async def delete_order(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Cancela (soft delete) um pedido pelo ID.
    Permissão: apenas admin ou dono do pedido.
    """
    pedido = session.query(Pedido).filter(Pedido.pedido_id == order_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    # Permissão: admin ou dono
    if not (current_user.admin or pedido.usuario_id == current_user.usuario_id):
        raise HTTPException(status_code=403, detail="Sem permissão para cancelar este pedido")
    pedido.status = StatusPedido.CANCELADO
    session.commit()
    # Retorna o pedido atualizado conforme o schema de saída
    return pedido

@order_router.post("/{order_id}/finalize", response_model=OrderOutSchema)
async def finalize_order(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Finaliza um pedido (status = ENTREGUE).
    Permissão: admin ou dono do pedido.
    Restrições: não permite finalizar se já estiver CANCELADO ou ENTREGUE.
    """
    try:
        pedido = session.query(Pedido).filter(Pedido.pedido_id == order_id).first()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")

        # Permissão: admin ou dono
        if not (current_user.admin or pedido.usuario_id == current_user.usuario_id):
            raise HTTPException(status_code=403, detail="Sem permissão para finalizar este pedido")

        # Restrições de estado
        if pedido.status == StatusPedido.CANCELADO:
            raise HTTPException(status_code=409, detail="Não é possível finalizar um pedido cancelado")
        if pedido.status == StatusPedido.ENTREGUE:
            raise HTTPException(status_code=409, detail="Pedido já finalizado")

        pedido.status = StatusPedido.ENTREGUE
        session.commit()
        return pedido
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao finalizar pedido. Tente novamente mais tarde.")

@order_router.post("/add-item/{order_id}", response_model=ItemPedidoOutSchema, status_code=201)
async def add_item_to_order(
    order_id: int,
    item_pedido_schema: ItemPedidoCreateSchema,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Adiciona um item a um pedido existente.
    Permissão: admin ou dono do pedido.
    """
    try:
        novo_item = svc_add_item(
            session=session,
            current_user=current_user,
            order_id=order_id,
            item_data=item_pedido_schema,
        )
        return novo_item
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao adicionar item ao pedido. Tente novamente mais tarde.")


@order_router.get("/{order_id}/items", response_model=list[ItemPedidoOutSchema])
async def list_order_items(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista itens de um pedido específico.
    Permissão: admin ou dono do pedido.
    Retorna 404 se o pedido não existir ou se não houver itens.
    """
    try:
        pedido = (
            session.query(Pedido)
            .filter(Pedido.pedido_id == order_id)
            .first()
        )
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")

        if not (current_user.admin or pedido.usuario_id == current_user.usuario_id):
            raise HTTPException(status_code=403, detail="Sem permissão para listar itens deste pedido")

        # Usa a tabela de itens diretamente; poderia usar pedido.itens com relationship
        itens = (
            session.query(ItensPedido)
            .filter(ItensPedido.pedido_id == order_id)
            .all()
        )
        if not itens:
            raise HTTPException(status_code=404, detail="Nenhum item encontrado")

        return itens
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao listar itens do pedido. Tente novamente mais tarde.")

@order_router.delete("/{order_id}/items/{item_id}", response_model=ItemPedidoOutSchema)
async def remove_order_item(
    order_id: int,
    item_id: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Remove um item específico de um pedido.
    Permissão: admin ou dono do pedido.
    Recalcula o total do pedido após remoção.
    """
    try:
        removed = svc_remove_item(
            session=session,
            current_user=current_user,
            order_id=order_id,
            item_id=item_id,
        )
        return removed
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover item do pedido: {e}")
