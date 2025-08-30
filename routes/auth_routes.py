from fastapi import APIRouter, Depends
from database.dependencies import get_session
from models.usuario_model import Usuario
from services.auth_service import user_auth
from utils.security import bcrypt_context, create_access_token, create_refresh_token
from schemas.usuario_schema import UsuarioSchema, UsuarioOutSchema
from sqlalchemy.orm import Session
from schemas.login_schema import LoginSchema
from schemas.token_schema import TokenResponseSchema
from fastapi import HTTPException
from database.dependencies import verify_refresh_bearer
from schemas.message_schema import MessageSchema

auth_router = APIRouter(prefix="/auth", tags=["auth"])

    
@auth_router.get("/", response_model=MessageSchema)
async def home():
    """
        Essa é um rota padrão de autenticação do nosso sistema
    """
    return {"mensagem": "Você acessou a rota de autenticação.", "autenticado": False}

@auth_router.post("/create_account", response_model=UsuarioOutSchema, status_code=201)
async def create_account(usuario_schema: UsuarioSchema, session: Session = Depends(get_session)):
    """
    Essa rota cria uma conta no sistema
    """
    senha_criptografada = bcrypt_context.hash(usuario_schema.senha)
    usuario = session.query(Usuario).filter(Usuario.email==usuario_schema.email).first()
    if usuario:
        raise HTTPException(status_code=409, detail="Usuario já existe.")
    else:
        novo_usuario = Usuario(usuario_schema.nome, usuario_schema.email, senha_criptografada, usuario_schema.ativo, usuario_schema.admin)
        session.add(novo_usuario)
        session.commit()
        session.refresh(novo_usuario)
        return novo_usuario

@auth_router.post("/login", response_model=TokenResponseSchema)
async def login(login_schema: LoginSchema, session: Session = Depends(get_session)):
    """
    Essa rota faz login no sistema
    """
    usuario = user_auth(login_schema.email, login_schema.senha, session)
    if not usuario:
        raise HTTPException(status_code=401, detail="Email ou senha invalidos ou usuario não encontrado.")
    else:
        token_data = {"sub": str(usuario.usuario_id)}
        acess_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return {"access_token": acess_token, "refresh_token": refresh_token, "token_type": "bearer"}

@auth_router.post("/refresh_token", response_model=TokenResponseSchema)
async def refresh_token(payload: dict = Depends(verify_refresh_bearer), session: Session = Depends(get_session)):
    """
    Essa rota faz refresh no token.
    Envie o refresh token no header Authorization: Bearer (use o botão Authorize → RefreshToken).
    """
    user_id = payload.get("sub")
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token invalido.")
    usuario = session.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Email ou senha invalidos ou usuario não encontrado.")

    token_data = {"sub": str(usuario.usuario_id)}
    acess_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    return {"access_token": acess_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
