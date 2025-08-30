from database.connection import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship

class ItensPedido(Base):
    __tablename__ = "itens_pedidos"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    pedido_id = Column("pedido_id", Integer, ForeignKey("pedidos.id"))
    nome_produto = Column("nome_produto", String)
    quantidade = Column("quantidade", Integer, default=1, nullable=False)
    preco_unitario = Column("preco_unitario", Numeric(10, 2), nullable=False)
    subtotal = Column("subtotal", Numeric(10, 2))
    # Relacionamento N:1 com Pedido
    pedido = relationship("Pedido", back_populates="itens")

