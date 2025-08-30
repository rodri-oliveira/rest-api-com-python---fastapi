from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.dependencies import get_session, get_current_user
from schemas.order_schema import OrderSchema, OrderOutSchema
from database.dependencies import verify_token
from models.pedido_model import Pedido
from models.usuario_model import Usuario
from fastapi import HTTPException
from models.pedido_model import StatusPedido


order_router = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(get_current_user)])

@order_router.get("", response_model=list[OrderOutSchema])
async def list_orders(session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    """
    Lista pedidos do usuário autenticado. Se admin, lista todos.
    """
    if getattr(current_user, "admin", False):
        pedidos = session.query(Pedido).all()
    else:
        pedidos = session.query(Pedido).filter(Pedido.usuario_id == current_user.usuario_id).all()
    return pedidos

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
    
