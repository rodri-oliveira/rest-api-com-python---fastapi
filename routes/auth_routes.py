from fastapi import APIRouter, Depends
from database.dependencies import get_session
from models.models import Usuario
from sqlalchemy import create_engine
from utils.security import bcrypt_context

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.get("/")
async def home():
    """
        Essa é um rota padrão de autenticação do nosso sistema
    """
    return {"Mendagem": "Voce acessou a de autenticação.", "autenticado": False}

@auth_router.post("/create_acount")
async def create_acount(email: str, senha: str, nome: str, session = Depends(get_session)):
    """
    Essa rota cria uma conta no sistema
    """
    senha_criptografada = bcrypt_context.hash(senha)
    usuario = session.query(Usuario).filter(Usuario.email==email).first()
    if usuario:
        return {"mensagem": "Usuario ja existe."}
    else:
        novo_usuario = Usuario(nome, email, senha_criptografada, ativo=True)
        session.add(novo_usuario)
        session.commit()
        return {"mensagem": "Usuario criado com sucesso."}