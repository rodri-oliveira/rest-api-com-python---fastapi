from pydantic import BaseModel

class MessageSchema(BaseModel):
    mensagem: str
    autenticado: bool = False
