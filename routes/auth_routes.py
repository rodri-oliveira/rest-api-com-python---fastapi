from fastapi import APIRouter, Depends
from database.dependencies import get_session
from models.usuario_model import Usuario
from services.auth_service import user_auth
from utils.security import bcrypt_context, create_access_token, create_refresh_token
from schemas.usuario_schema import UsuarioSchema
from sqlalchemy.orm import Session
from schemas.login_schema import LoginSchema
from fastapi import HTTPException
from utils.security import verify_token

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
        refresh_token = create_refresh_token(token_data)
        return {"access_token": acess_token, "refresh_token": refresh_token, "token_type": "bearer"}

@auth_router.post("/refresh_token")
async def refresh_token(refresh_token: str, session: Session = Depends(get_session)):
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token invalido.")

    email = payload.get("sub")
    usuario = session.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Email ou senha invalidos ou usuario não encontrado.")

    token_data = {"sub": usuario.email}
    acess_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    return {"access_token": acess_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
