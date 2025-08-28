from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

# Configuração do banco de dados SQLite
# O caminho pode ser ajustado conforme necessário

db = create_engine("sqlite:///database/database.db")
Base = declarative_base()
