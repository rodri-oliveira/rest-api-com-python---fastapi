# FastAPI Modular Starter

Um template inicial para criar APIs modulares com FastAPI, SQLAlchemy, Alembic (migrações), Pydantic v2, autenticação (JWT) e testes com Pytest. Serve como base genérica e educativa para iniciar novos projetos.


## Sumário
- Visão geral
- Principais recursos
- Arquitetura e organização de pastas
- Requisitos
- Configuração do ambiente
- Variáveis de ambiente
- Execução da aplicação
- Banco de dados e migrações (Alembic)
- Testes (Pytest)
- Convenções de commits (pt-BR)
- Dicas e boas práticas
- Troubleshooting


## Visão geral
Este projeto demonstra uma arquitetura em camadas:
- Rotas (FastAPI) focadas em entrada/saída HTTP
- Serviços com as regras de negócio
- Modelos (SQLAlchemy) e Schemas (Pydantic v2)
- Dependências de banco (sessão) e segurança (hash/JWT)
- Testes isolados com engine SQLite in-memory e StaticPool


## Principais recursos
- FastAPI com routers modulares
- SQLAlchemy 2.0 (ORM)
- Alembic para migrações
- Pydantic v2 (ConfigDict) para validações
- Autenticação JWT com python-jose
- Testes com pytest + httpx


## Arquitetura e organização de pastas
```
project/
├── alembic/
│   └── versions/
├── database/
│   ├── connection.py         # Engine/Session/Base
│   └── dependencies.py       # get_session, get_current_user
├── models/
│   ├── usuario_model.py
│   ├── pedido_model.py
│   └── item_pedido_model.py
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py
│   └── order_routes.py
├── schemas/
│   ├── usuario_schema.py
│   ├── login_schema.py
│   ├── token_schema.py
│   ├── order_schema.py
│   └── itemOrder_schema.py
├── services/
│   ├── auth_service.py
│   └── order_service.py
├── utils/
│   └── security.py
├── tests/
│   └── test_orders.py
├── alembic.ini
├── main.py
├── requirement.txt
└── .gitignore
```


## Requisitos
- Python 3.11+
- Git

Opcional:
- Docker/Docker Compose (para DB e execução em contêiner)


## Configuração do ambiente
1) Criar e ativar o ambiente virtual (Windows PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2) Instalar dependências:
```powershell
pip install -r requirement.txt
```


## Variáveis de ambiente
Crie um arquivo `.env` (não versionado) com, por exemplo:
```
SECRET_KEY=troque-esta-chave
ACCESS_TOKEN_EXPIRE_MINUTES=30
# Exemplo SQLite local
DATABASE_URL=sqlite:///./app.db
# Exemplo Postgres
# DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/minha_base
```
Carregue via `python-dotenv` (se necessário) no bootstrap da aplicação.


## Execução da aplicação
- Rodar localmente com hot reload:
```powershell
uvicorn main:app --reload
```
- Abrir documentação interativa (Swagger):
```
http://localhost:8000/docs
```


## Banco de dados e migrações (Alembic)
1) Inicializar Alembic (caso ainda não exista a pasta):
```powershell
alembic init alembic
```

2) Configurar `alembic.ini`/`alembic/env.py` para apontar para `DATABASE_URL`/engine do projeto.

3) Criar uma migração:
```powershell
alembic revision -m "minha primeira migracao"
```

4) Aplicar migrações:
```powershell
alembic upgrade head
```

Dicas:
- Use autogenerate com cautela; sempre revise o script gerado.
- Mantenha migrações pequenas e frequentes.


## Testes (Pytest)
- Rodar todos os testes:
```powershell
python -m pytest
```
- Rodar com saída compacta:
```powershell
python -m pytest -q
```
- Filtrar por substring do nome:
```powershell
python -m pytest -k add_item
```

Notas de testes:
- A suíte usa `sqlite:///:memory:` com `StaticPool` para compartilhar a mesma conexão entre threads do TestClient, evitando erros como "no such table".
- Overrides de dependências permitem injetar sessão de teste e usuário autenticado fake.


## Convenções de commits (pt-BR)
Use Conventional Commits em português. Exemplos:
- `feat(auth): adicionar rota de login com JWT`
- `fix(orders): corrigir recálculo de total ao remover item`
- `chore(pydantic): migrar Config para ConfigDict (Pydantic v2)`
- `refactor(orders): simplificar serviço de pedidos`
- `test(orders): adicionar casos de finalização e permissões`

Fluxo Git sugerido:
- Branches por feature: `feature/nome-da-feature`
- PRs com revisão e CI rodando `pytest`


## Dicas e boas práticas
- Mantener regras de negócio em `services/` (facilita testes e reuso)
- Validar campos com Pydantic v2 (`Annotated`, `condecimal`, `conint`)
- Evitar lógica pesada nas rotas; rotas orquestram, serviços executam
- Registrar decisões arquiteturais (ADR) ou em `docs/`
- Usar `Decimal` para valores monetários


## Troubleshooting
- Erro `no such table` nos testes: garanta `StaticPool` no engine SQLite in-memory
- `RuntimeError: httpx não instalado`: `pip install httpx`
- Warnings do Pydantic v2 sobre `class Config`: migre para `ConfigDict`
- Problemas de import: verifique `PYTHONPATH` e estrutura de pacotes

---

Sinta-se livre para forkar e adaptar este starter às necessidades do seu domínio. Contributions e PRs são bem-vindos!
