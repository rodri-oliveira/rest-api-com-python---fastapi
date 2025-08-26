from fastapi import APIRouter

order_router = APIRouter(prefix="/orders", tags=["orders"])

@order_router.get("/")
async def orders():
    """
        Essa é uma rota padrão de pedidos do nosso sistemas, todas as rotas de pedidos precisa de autenticação
    """
    return {"mensagem": "Você acessou a rota de pedidos."}