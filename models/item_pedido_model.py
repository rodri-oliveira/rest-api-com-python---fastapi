from database.connection import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey

class ItensPedido(Base):
    __tablename__ = "itens_pedidos"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    pedido_id = Column("pedido_id", Integer, ForeignKey("pedidos.id"))
    nome_produto = Column("nome_produto", String)
    quantidade = Column("quantidade", Integer, default=1, nullable=False)
    preco_unitario = Column("preco_unitario", Float, nullable=False)
    subtotal = Column("subtotal", Float)

    def __init__(self, pedido_id, nome_produto, quantidade=1, preco_unitario=0.0, subtotal=0.0):
        self.pedido_id = pedido_id
        self.nome_produto = nome_produto
        self.quantidade = quantidade
        self.preco_unitario = preco_unitario
        self.subtotal = subtotal
