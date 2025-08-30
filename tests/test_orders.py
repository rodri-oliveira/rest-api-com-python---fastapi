import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from decimal import Decimal

from main import app
from database.connection import Base
from database.dependencies import get_session, get_current_user
from models.usuario_model import Usuario
from models.pedido_model import StatusPedido


@pytest.fixture()
def engine():
    # Banco em memória compartilhado entre conexões/threads
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture()
def SessionLocal(engine):
    return sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db(engine):
    # Recria o schema a cada teste
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(SessionLocal):
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    # Override da sessão do app para usar o banco de teste
    def override_get_session():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_session] = override_get_session
    c = TestClient(app)
    try:
        yield c
    finally:
        app.dependency_overrides.pop(get_session, None)


def _make_user(db_session, nome="user", email="user@test.com", admin=False, ativo=True) -> Usuario:
    u = Usuario(nome=nome, email=email, senha="hash", ativo=ativo, admin=admin)
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


def _override_user(user: Usuario):
    def _dep():
        return user
    return _dep


def _auth_headers():
    # Como get_current_user está sobrescrito, o valor do Authorization não é checado.
    return {"Authorization": "Bearer test"}


def test_create_and_list_my_orders(client, db_session):
    user = _make_user(db_session)
    app.dependency_overrides[get_current_user] = _override_user(user)

    # Cria dois pedidos
    res1 = client.post("/orders", json={"preco": "10.00"}, headers=_auth_headers())
    assert res1.status_code == 200
    res2 = client.post("/orders", json={"preco": "20.50"}, headers=_auth_headers())
    assert res2.status_code == 200

    # Lista meus pedidos
    res = client.get("/orders/my", headers=_auth_headers())
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert {Decimal(d["preco"]) for d in data} == {Decimal("10.00"), Decimal("20.50")}

    app.dependency_overrides.pop(get_current_user, None)


def test_add_and_remove_item_recalculates_total(client, db_session):
    user = _make_user(db_session)
    app.dependency_overrides[get_current_user] = _override_user(user)

    # Cria pedido base com preco inicial 0.00
    res = client.post("/orders", json={"preco": "0.01"}, headers=_auth_headers())
    assert res.status_code == 200
    order_id = res.json()["pedido_id"]

    # Adiciona itens
    add1 = client.post(
        f"/orders/add-item/{order_id}",
        json={"nome_produto": "lapis", "quantidade": 2, "preco_unitario": "3.00"},
        headers=_auth_headers(),
    )
    assert add1.status_code == 201
    add2 = client.post(
        f"/orders/add-item/{order_id}",
        json={"nome_produto": "caneta", "quantidade": 1, "preco_unitario": "2.50"},
        headers=_auth_headers(),
    )
    assert add2.status_code == 201

    # Total esperado: 2*3.00 + 1*2.50 = 8.50
    get_order = client.get(f"/orders/{order_id}", headers=_auth_headers())
    assert get_order.status_code == 200
    assert Decimal(get_order.json()["preco"]) == Decimal("8.50")

    # Lista itens
    list_items = client.get(f"/orders/{order_id}/items", headers=_auth_headers())
    assert list_items.status_code == 200
    items = list_items.json()
    assert len(items) == 2

    # Remove um item (o segundo)
    item_id = items[1]["id"]
    rem = client.delete(f"/orders/{order_id}/items/{item_id}", headers=_auth_headers())
    assert rem.status_code == 200

    # Total atualizado: 8.50 - 2.50 = 6.00
    get_order2 = client.get(f"/orders/{order_id}", headers=_auth_headers())
    assert get_order2.status_code == 200
    assert Decimal(get_order2.json()["preco"]) == Decimal("6.00")

    app.dependency_overrides.pop(get_current_user, None)


def test_finalize_order_happy_path(client, db_session):
    user = _make_user(db_session)
    app.dependency_overrides[get_current_user] = _override_user(user)

    # Cria pedido
    res = client.post("/orders", json={"preco": "0.01"}, headers=_auth_headers())
    assert res.status_code == 200
    order_id = res.json()["pedido_id"]

    # Finaliza
    fin = client.post(f"/orders/{order_id}/finalize", headers=_auth_headers())
    assert fin.status_code == 200
    assert fin.json()["status"] == StatusPedido.ENTREGUE.value

    # Tenta finalizar de novo → 409
    fin2 = client.post(f"/orders/{order_id}/finalize", headers=_auth_headers())
    assert fin2.status_code == 409

    app.dependency_overrides.pop(get_current_user, None)


def test_permissions_and_status_conflicts(client, db_session):
    # Cria dois usuários: dono e outro
    owner = _make_user(db_session, nome="owner", email="o@test.com")
    other = _make_user(db_session, nome="other", email="x@test.com")

    # Dono cria pedido
    app.dependency_overrides[get_current_user] = _override_user(owner)
    res = client.post("/orders", json={"preco": "0.01"}, headers=_auth_headers())
    assert res.status_code == 200
    order_id = res.json()["pedido_id"]

    # Outro usuário tenta finalizar → 403
    app.dependency_overrides[get_current_user] = _override_user(other)
    fin_forbidden = client.post(f"/orders/{order_id}/finalize", headers=_auth_headers())
    assert fin_forbidden.status_code == 403

    # Dono cancela e depois tenta finalizar → 409
    app.dependency_overrides[get_current_user] = _override_user(owner)
    cancel = client.delete(f"/orders/{order_id}", headers=_auth_headers())
    assert cancel.status_code == 200

    fin_conflict = client.post(f"/orders/{order_id}/finalize", headers=_auth_headers())
    assert fin_conflict.status_code == 409

    app.dependency_overrides.pop(get_current_user, None)
