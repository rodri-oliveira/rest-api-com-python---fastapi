from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base
from enum import Enum
from sqlalchemy import Enum as SqlEnum

db = create_engine("sqlite:///database/database.db")
Base = declarative_base()

class StatusPedido(Enum):
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"

# criar as classes/tabelas  do banco de dados
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    nome = Column("nome", String)
    email = Column("email", String, nullable=False, unique=True)
    senha = Column("senha", String)
    ativo = Column("ativo", Boolean)
    admin = Column("admin", Boolean, default=False)

    def __init__(self, nome, email, senha, ativo=True, admin=False):
        self.nome = nome
        self.email = email
        self.senha = senha
        self.ativo = ativo
        self.admin = admin

class Pedido(Base):
    __tablename__= "pedidos"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    status = Column("status", SqlEnum(StatusPedido))
    usuario_id = Column("usuario_id", Integer, ForeignKey("usuarios.id"))
    preco = Column("preco", Float)

    def __init__(self, usuario_id, preco, status=StatusPedido.PENDENTE):
        self.usuario_id = usuario_id
        self.preco = preco
        self.status = status

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



