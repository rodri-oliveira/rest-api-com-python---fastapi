from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.get("/")
async def auth():
    """
        Essa é um rota padrão de autenticação do nosso sistema
    """
    return {"Mendagem": "Voce acessou a de autenticação.", "autenticado": False}