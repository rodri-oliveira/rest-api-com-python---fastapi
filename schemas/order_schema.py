from pydantic import BaseModel


class OrderSchema(BaseModel):
    usuario_id: int

    class Config:
        from_attributes = True
