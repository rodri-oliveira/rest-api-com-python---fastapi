from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.dependencies import get_session
from schemas.order_schema import OrderSchema
from models.pedido_model import Pedido
from models.usuario_model import Usuario
from fastapi import HTTPException


order_router = APIRouter(prefix="/orders", tags=["orders"])

@order_router.get("/")
async def orders():
    """
        Essa é uma rota padrão de pedidos do nosso sistemas, todas as rotas de pedidos precisa de autenticação
    """
    return {"mensagem": "Você acessou a rota de pedidos."}

@order_router.post("/order")
async def create_order(order_schema: OrderSchema, session: Session = Depends(get_session)):
    """
    Essa rota cria um pedido no sistema
    """
    usuario_schema = session.query(Usuario).filter(Usuario.usuario_id == order_schema.usuario_id).first()
    if not usuario_schema:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    
    new_order = Pedido(usuario_schema.usuario_id, order_schema.usuario_id)
    session.add(new_order)
    session.commit()
    return {"mensagem": f"Pedido criado com sucesso.", "order_id": new_order.usuario_id}