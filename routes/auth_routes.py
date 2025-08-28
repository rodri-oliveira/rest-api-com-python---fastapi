from fastapi import APIRouter, Depends
from database.dependencies import get_session
from models.usuario_model import Usuario
from services.auth_service import user_auth
from utils.security import bcrypt_context
from schemas.usuario_schema import UsuarioSchema
from sqlalchemy.orm import Session
from schemas.login_schema import LoginSchema
from jose import jwt
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
    usuario = user_auth(login_schema.email, login_schema.senha, session)
    if not usuario:
        raise HTTPException(status_code=401, detail="Email ou senha invalidos ou usuario não encontrado.")
    else:
        token_data = {"sub": usuario.email}
        acess_token = create_access_token(token_data)
        return {"acess_token": acess_token, "token_type": "bearer"}