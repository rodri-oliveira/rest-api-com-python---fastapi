from utils.security import bcrypt_context
from models.usuario_model import Usuario

def user_auth(email: str, senha: str, session):
    usuario = session.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        return False
    if not bcrypt_context.verify(senha, usuario.senha):
        return False
    return usuario