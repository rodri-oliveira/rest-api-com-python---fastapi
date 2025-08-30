from pydantic import BaseModel, ConfigDict
from typing import Optional

class UsuarioSchema(BaseModel):
    nome: str
    email: str
    senha: str
    ativo: Optional[bool] = True
    admin: Optional[bool] = False
    model_config = ConfigDict(from_attributes=True)


class UsuarioOutSchema(BaseModel):
    usuario_id: int
    nome: str
    email: str
    ativo: bool
    admin: bool
    model_config = ConfigDict(from_attributes=True)
