from database.connection import Base
from sqlalchemy import Column, Integer, Float, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from enum import Enum
from sqlalchemy import Enum as SqlEnum

class StatusPedido(Enum):
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"

class Pedido(Base):
    __tablename__= "pedidos"

    pedido_id = Column("id", Integer, primary_key=True, autoincrement=True)
    status = Column("status", SqlEnum(StatusPedido))
    usuario_id = Column("usuario_id", Integer, ForeignKey("usuarios.id"))
    preco = Column("preco", Numeric(10, 2))
    # Relacionamento 1:N com ItensPedido
    itens = relationship(
        "ItensPedido",
        back_populates="pedido",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __init__(self, usuario_id, preco, status=StatusPedido.PENDENTE):
        self.usuario_id = usuario_id
        self.preco = preco
        self.status = status
