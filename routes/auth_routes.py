from fastapi import APIRouter, Depends
from database.dependencies import get_session
from models.usuario_model import Usuario
from sqlalchemy import create_engine
from utils.security import bcrypt_context
from schemas.usuario_schema import UsuarioSchema
from sqlalchemy.orm import Session
from schemas.login_schema import LoginSchema
from jose import JWTError, jwt
from datetime import datetime, timedelta
from utils.security import create_access_token
from fastapi import HTTPException

auth_router = APIRouter(prefix="/auth", tags=["auth"])

    
@auth_router.get("/")
async def home():
    """
        Essa é um rota padrão de autenticação do nosso sistema
    """
    return {"Mendagem": "Voce acessou a de autenticação.", "autenticado": False}

@auth_router.post("/create_acount")
async def create_acount(usuario_schema: UsuarioSchema, session: Session = Depends(get_session)):
    """
    Essa rota cria uma conta no sistema
    """
    senha_criptografada = bcrypt_context.hash(usuario_schema.senha)
    usuario = session.query(Usuario).filter(Usuario.email==usuario_schema.email).first()
    if usuario:
        return {"mensagem": "Usuario ja existe."}
    else:
        novo_usuario = Usuario(usuario_schema.nome, usuario_schema.email, senha_criptografada, usuario_schema.ativo, usuario_schema.admin)
        session.add(novo_usuario)
        session.commit()
        return {"mensagem": f"Usuario {usuario_schema.nome} criado com sucesso.", "email": usuario_schema.email}

@auth_router.post("/login")
async def login(login_schema: LoginSchema, session: Session = Depends(get_session)):
    """
    Essa rota faz login no sistema
    """
    usuario = session.query(Usuario).filter(Usuario.email==login_schema.email).first()
    if not usuario or not bcrypt_context.verify(login_schema.senha, usuario.senha):
        raise HTTPException(status_code=401, detail="Email ou senha invalidos")
    else:
        token_data = {"sub": usuario.email}
        acess_token = create_access_token(token_data)
        return {"acess_token": acess_token, "token_type": "bearer"}